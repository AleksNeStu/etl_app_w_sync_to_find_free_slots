"""Load meet data to DB."""
import datetime
import json
import logging
import os
# noinspection PyPackageRequirements,PyPackageRequirements
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

# add_module_to_sys_path
import pytz

from data.models.syncs import Sync
from enums.sa import SyncStatus
from services import sync_service
from utils.py import DictToObj

directory = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, directory)

import settings
import data.db_session as db_session

req, resp, last_sync, actual_sync, errors = None, None, None, None, []

def run():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logging.info("Load meet data to DB")

    load_results = {"Load meet data is done"}
    remote_data = get_remote_data()
    # TODO: Fill sync statuses

    # TODO: Add logic to pars remote_data e.g. using pandas


    return load_results

def is_new_data_for_sync(session):
    global last_sync, actual_sync, req, resp, errors

    req = Request(settings.SYNC_DATA_URL)
    actual_sync = Sync(
        start_date=datetime.datetime.now(),
        status=SyncStatus.in_progress
    )

    session.add(actual_sync)
    last_sync = sync_service.get_latest_finished_sync(session)

    if last_sync:
        # resp_headers = DictToObj(
        #     default_val=None, **last_sync.resp_headers)
        # TODO: Add generic API checks.
        # Suppose to use API contract of AWS.
        # https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/
        # RequestAndResponseBehaviorS3Origin.html
        req.add_header('If-Match', last_sync.resp_headers.get('ETag'))
        req.add_header('If-Modified-Since',
                       last_sync.resp_headers.get('Last-Modified'))
        try:
            resp = urlopen(req)
            return True
        #TODO: Exdent error handling.
        except Exception as err:
            actual_sync.end_date = datetime.datetime.now()
            actual_sync.resp_headers = dict(getattr(err, 'headers', {}))
            # Skip due to not modified 304 status code (no new content)
            if type(err) == HTTPError and err.status == 304:
                actual_sync.status = SyncStatus.skipped

            # Skip due to errors.
            else:
                # TODO: Consider avoid of the infinite loop.
                logging.error(
                    f'Error on try to load remote meet data: {err}')
                errors.append(str(err))
                actual_sync.errors = errors
                actual_sync.status = SyncStatus.errors

            session.commit()
            return False

    session.commit()

    return True


def get_remote_data():
    global last_sync, actual_sync, req, resp, errors

    with db_session.create_session() as session:
        if is_new_data_for_sync(session):
            try:
                resp = resp or urlopen(req)
                content = resp.read()
                actual_sync.end_date = datetime.datetime.now()
                actual_sync.resp_headers = dict(getattr(resp, 'headers', {}))
                actual_sync.status = SyncStatus.finished
                session.commit()
                return content

            except Exception as err:
                # TODO: Add more precise error handling
                errors.append(str(err))
                actual_sync.errors = errors
                actual_sync.status = SyncStatus.errors
                session.commit()
                logging.error(f'Error on try to load remote meet data: {err}')

    # Set to None globals shares after each sync
    req, resp, last_sync, actual_sync, errors = None, None, None, None, []


def setup_db():
    db_session.init_sql(settings.DB_CONNECTION)


if __name__ == '__main__':
    run()