"""Load remote meet data to DB."""
import copy
import datetime
import json
import logging
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from data.models.syncs import Sync
from enums.sa import SyncStatus, SyncEndReason
from services import sync_service
from utils import py as py_utils

# add_module_to_sys_path
directory = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, directory)

import settings
import data.db_session as db_session

# `results` is related only to data parsing.
req, resp, last_sync, actual_sync, errors, parsing_results = (
    None, None, None, None, [], {})


#TODO: results w/ structure like dict items, errors w/o structure
def run():
    global last_sync, actual_sync, req, resp, errors, parsing_results

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logging.info("Load meet data to DB")

    actual_sync_kwargs = {}
    sync = None

    with db_session.create_session() as session:
        remote_data = get_remote_data(session)
        if remote_data:
            # Parsing and storing to DB got data.
            # TODO: Add logic to pars remote_data e.g. using pandas

            # Store parsing results.
            actual_sync_kwargs.update(**dict(
                end_date=datetime.datetime.now(),
                status=SyncStatus.finished,
                end_reason=SyncEndReason.data_parsing_end,
                parsing_results=parsing_results))
            py_utils.set_obj_attr_values(actual_sync, actual_sync_kwargs)
            session.commit()

    sync = copy.deepcopy(actual_sync)
    # Set to None globals shares after each sync
    req, resp, last_sync, actual_sync, errors = None, None, None, None, []

    return sync


def is_new_data_for_sync(session):
    global last_sync, actual_sync, req, resp, errors

    req = Request(settings.SYNC_DATA_URL)
    actual_sync = Sync(
        start_date=datetime.datetime.now(),
        status=SyncStatus.started
    )

    session.add(actual_sync)
    # sync_service.get_sync(get_kwargs={'id': 1}, session=session)
    last_sync = sync_service.get_latest_finished_sync(session)

    if last_sync:
        actual_sync_kwargs = {}
        # resp_headers = DictToObj(
        #     default_val=None, **last_sync.resp_headers)
        # TODO: Add generic API checks.
        # Suppose to use API contract of AWS.
        # https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/
        # RequestAndResponseBehaviorS3Origin.html
        last_sync_headers = json.loads(last_sync.resp_headers)
        req.add_header('If-Match', last_sync_headers.get('ETag'))
        req.add_header('If-Modified-Since',
                       last_sync_headers.get('Last-Modified'))
        try:
            resp = urlopen(req)
            return True

        #TODO: Exdent error handling.
        except Exception as err:
            error_msg = f'Error on try to load remote meet data: {err}'
            errors.append(error_msg)
            actual_sync_kwargs.update(**dict(
                end_date=datetime.datetime.now(),
                resp_headers=dict(getattr(err, 'headers', {})),
                errors=[error_msg]))

            # Skip due to not modified 304 status code (no new content)
            if type(err) == HTTPError and err.status == 304:
                actual_sync_kwargs.update(**dict(
                    status=SyncStatus.skipped,
                    end_reason=SyncEndReason.no_new_remote_data))
                logging.warning(error_msg)

            else:
                actual_sync_kwargs.update(**dict(
                    status=SyncStatus.errors,
                    end_reason=SyncEndReason.remote_server_errors))
                logging.error(error_msg)
                raise err

            py_utils.set_obj_attr_values(actual_sync, actual_sync_kwargs)
            session.commit()

            return False

    session.commit()

    return True


def get_remote_data(session):
    global last_sync, actual_sync, req, resp, errors

    if is_new_data_for_sync(session):
        actual_sync_kwargs = {}
        try:
            resp = resp or urlopen(req)
            content = resp.read()

            py_utils.set_obj_attr_values(
                actual_sync, dict(
                    resp_headers=dict(getattr(resp, 'headers', {})),
                    status=SyncStatus.got_data))
            session.commit()

            return content

        # TODO: Add more precise error handling.
        except Exception as err:
            error_msg = (
                f'Error on try to request: {req} remote meet data: {err}')
            errors.append(error_msg)
            logging.error(error_msg)

            actual_sync_kwargs.update(**dict(
                end_date=datetime.datetime.now(),
                status=SyncStatus.errors,
                end_reason=SyncEndReason.remote_server_errors))
            py_utils.set_obj_attr_values(actual_sync, actual_sync_kwargs)
            py_utils.update_obj_attr_values(
                actual_sync, dict(errors=[error_msg]))
            session.commit()

    return


def setup_db():
    db_session.init_sql(settings.DB_CONNECTION)


if __name__ == '__main__':
    run()