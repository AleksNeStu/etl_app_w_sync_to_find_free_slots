"""Load remote meet data to DB."""
import copy
import datetime
import json
import logging
import os
import sys
from io import StringIO
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pandas as pd

from data.models.syncs import Sync, NotSyncedItem
from data.models.users import User
from enums.sa import SyncStatus, SyncEndReason, NotSyncedItemReason
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

#TODO: Consider cases when hashes for users and meets are not consinstent
# from 3rd party server (need to assign internal checks using utils.db.to_hash
# or more simple md5)
#TODO: Add type hints
#TODO: Consider avoid using global scope vars
#TODO: Add progressbar flow
#TODO: Refactor module and extract based on responsibility parts
#TODO: Add proper logging and errors, results collecting
def run(sync_type, forced=False):
    """
    # Not used pandas.DataFrame.to_sql approach which allows quickly
    # complete the task even skip duplicates, but applied collecting
    # all items more accurate, e.g. for future investigation purposes
    # as well as make consistent solution with ORM models across whole
    # project.
    # engine = db_session.create_engine()
    # df_users.to_sql('superstore', engine)
    """
    global last_sync, actual_sync, req, resp, errors, parsing_results

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logging.info("Load meet data to DB")

    actual_sync_kwargs = {}
    sync = None

    with db_session.create_session() as session:
        remote_data = get_remote_data(session, forced, sync_type)
        if remote_data:
            # Parsing and storing to DB got data.
            df_users, df_meets = extract_pandas_data_frames(remote_data)

            # Storing users data to DB.
            db_users_synced, db_not_synced_items_users = insert_df_users_to_db(
                session, df_users)

            # Storing meets data to DB.
            db_meets_synced, db_not_synced_items_meets = insert_df_meets_to_db(
                session, df_meets)

            #TODO: Log results of DB inserting

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


def insert_df_users_to_db(session, df_users):
    logging.info("Inserting users data to DB")

    (df_users_unique, df_users_duplicated_data,
     df_users_duplicated_none) = aggregate_users_df(df_users)

    # Inset new portion of unique users.
    sync_users = build_sync_users(session, df_users_unique)
    session.add_all(sync_users)

    # Insert not synced users items (not checking previous syncs even for
    # forced options), meaning every sync will produce adding probably
    # duplications but provided info for investigations.
    sync_users_duplicated_data_items = build_sync_not_synced_items(
        df_users_duplicated_data, NotSyncedItemReason.duplicated_data.value)
    session.add_all(sync_users_duplicated_data_items)
    sync_users_duplicated_none_items = build_sync_not_synced_items(
        df_users_duplicated_none, NotSyncedItemReason.duplicated_none.value)
    session.add_all(sync_users_duplicated_none_items)

    session.commit()

    db_not_synced_items_users = list(py_utils.flatten(
        [sync_users_duplicated_data_items, sync_users_duplicated_none_items]))
    logging.info("Inserting users data to DB is finished.")

    return sync_users, db_not_synced_items_users

def insert_df_meets_to_db(session, df_meets):
    logging.info("Inserting user meets data to DB")

    (df_meets_unique, df_meets_duplicated_data,
     df_meets_duplicated_none) = aggregate_meets_df(df_meets)

    # # Inset new portion of unique meets.
    # sync_meets = build_sync_meets(session, df_meets_unique)
    # session.add_all(sync_meets)
    #
    # # Insert not synced meets items (not checking previous syncs even for
    # # forced options), meaning every sync will produce adding probably
    # # duplications but provided info for investigations.
    # sync_users_duplicated_data_items = build_sync_not_synced_items(
    #     df_meets_duplicated_data, NotSyncedItemReason.duplicated_data.value)
    # session.add_all(sync_users_duplicated_data_items)
    # sync_users_duplicated_none_items = build_sync_not_synced_items(
    #     df_meets_duplicated_none, NotSyncedItemReason.duplicated_none.value)
    # session.add_all(sync_users_duplicated_none_items)
    #
    # session.commit()
    #
    # db_not_synced_items_meets = list(py_utils.flatten(
    #     [sync_users_duplicated_data_items, sync_users_duplicated_none_items]))
    # logging.info("Inserting meets data to DB is finished.")
    #
    # return sync_meets, db_not_synced_items_meets
    return None, None


def build_sync_users(session, df_users):
    global actual_sync
    users = []
    # df_users_unique_kwargs = df_users.to_dict('records')
    for user in df_users.itertuples():
        #TODO: Avoid sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError)
        # UNIQUE constraint failed: users.hash_id e.g. force sync with the same
        # data.
        u = User.as_unique(
            session=session,
            hash_id=user.user_id)
        u.name = user.user_name
        u.sync_id = actual_sync.id
        users.append(u)

    return users

def build_sync_not_synced_items(df_not_synced, reason):
    global actual_sync

    return [
        NotSyncedItem(
            sync_id=actual_sync.id,
            item_data=json.dumps(not_synced_dict),
            reason=reason
        )
        for not_synced_dict in df_not_synced.to_dict('records')]


def aggregate_users_df(df_users):
    # TODO: Add cases to choose name from name and none values, like, for now
    #  first is taken
    # 320426673944415970493216791331086532677,Tami Black
    # 320426673944415970493216791331086532677,nan
    # user_id, user_name
    dup_subset = ['user_id']
    df_users_unique = df_users.drop_duplicates(
        subset=dup_subset, keep='first').dropna().sort_values('user_name')  # 140

    df_duplicates_all = df_users[df_users.duplicated(
        subset=dup_subset, keep=False)].sort_values('user_name')  # 9

    # Duplicates (add to `not_synced_items` table)
    # 160958802196100808578296561932835503894,Elizabeth Bravo
    # 300760312550512860711662300860730112051,Edward Winfield
    df_duplicated_data = df_duplicates_all[df_duplicates_all.duplicated(
        subset=dup_subset, keep='first')].dropna().sort_values('user_name')  # 2

    # Not duplicates (add to `user` table):
    # 160958802196100808578296561932835503894,Elizabeth Bravo
    # 300760312550512860711662300860730112051,Edward Winfield
    # 320426673944415970493216791331086532677,Tami Black
    df_not_duplicated = df_duplicates_all.drop_duplicates(
        subset=dup_subset, keep='first').dropna().sort_values('user_name')  # 3

    # None (add to `not_synced_items` table):
    # 320426673944415970493216791331086532677,nan
    # None,None
    # None,None
    # None,None
    df_duplicated_none = df_duplicates_all[
        df_duplicates_all.isnull().any(axis=1)].sort_values('user_name')  # 4

    df_duplicates_all_count=len(df_duplicates_all.index) # 9
    # 9 = 2 + 3 + 4
    df_duplicated_data_count=len(df_duplicated_data.index) # 2
    df_not_duplicated_count=len(df_not_duplicated.index) # 3
    df_duplicated_none_count=len(df_duplicated_none.index) # 4

    users_kwargs = dict(
        users_duplicates_all_count=df_duplicates_all_count,
        users_duplicated_data_count=df_duplicated_data_count,
        users_not_duplicated_count=df_not_duplicated_count,
        users_duplicated_none_count=df_duplicated_none_count,
    )
    parsing_results.update(users_kwargs)
    df_duplicates_all_collected = pd.concat([
        df_duplicated_data,
        df_not_duplicated,
        df_duplicated_none]).sort_values('user_name')
    if not df_duplicates_all.reset_index(drop=True).equals(
            df_duplicates_all_collected.reset_index(drop=True)):
        raise (f'Pandas users dataframes analyzing error due to diff count '
               f'of rows: {users_kwargs}')

    return df_users_unique, df_duplicated_data, df_duplicated_none


def aggregate_meets_df(df_meets):
    # user_id, meet_start_date. meet_end_date, meet_id
    dup_subset = ['user_id', 'meet_start_date', 'meet_end_date']
    df_meets_unique = df_meets.drop_duplicates(
        subset=dup_subset,
        keep='first').dropna().sort_values('meet_start_date') # 10078

    df_duplicates_all = df_meets[df_meets.duplicated(
        subset=dup_subset, keep=False)].sort_values('meet_start_date')  # 0

    # Duplicates (add to `not_synced_items` table)
    df_duplicated_data = df_duplicates_all[df_duplicates_all.duplicated(
        subset=dup_subset,
        keep='first')].dropna().sort_values('meet_start_date')  # 0

    # Not duplicates (add to `meet` table):
    df_not_duplicated = df_duplicates_all.drop_duplicates(
        subset=dup_subset,
        keep='first').dropna().sort_values('meet_start_date')  # 0

    # None (add to `not_synced_items` table):
    df_duplicated_none = df_duplicates_all[
        df_duplicates_all.isnull().any(axis=1)].sort_values('meet_start_date')  # 0

    df_duplicates_all_count=len(df_duplicates_all.index) # 9
    # 9 = 2 + 3 + 4
    df_duplicated_data_count=len(df_duplicated_data.index) # 2
    df_not_duplicated_count=len(df_not_duplicated.index) # 3
    df_duplicated_none_count=len(df_duplicated_none.index) # 4

    meets_kwargs = dict(
        meets_duplicates_all_count=df_duplicates_all_count,
        meets_duplicated_data_count=df_duplicated_data_count,
        meets_not_duplicated_count=df_not_duplicated_count,
        meets_duplicated_none_count=df_duplicated_none_count,
    )
    parsing_results.update(meets_kwargs)
    df_duplicates_all_collected = pd.concat([
        df_duplicated_data,
        df_not_duplicated,
        df_duplicated_none]).sort_values('meet_start_date')
    if not df_duplicates_all.reset_index(drop=True).equals(
            df_duplicates_all_collected.reset_index(drop=True)):
        raise (f'Pandas meets dataframes analyzing error due to diff count '
               f'of rows: {meets_kwargs}')

    return df_meets_unique, df_duplicated_data, df_duplicated_none


def extract_pandas_data_frames(remote_data):
    """
    Skip convertin datetime related columns to datetime, cause pandas in case
    of all parsed rows is convertin type o column to datetime64 even
    dateparse returns datetime. If try to convert datetime64 to datetime
    using x.astype(datetime.datetime) return int instead of datetime.
    Additionally issue with store d64 to datetime sa columns.

    df_meets['meet_start_date'] = df_meets['meet_start_date'].apply(dateparse)
    df_meets['meet_end_date'] = df_meets['meet_end_date'].apply(dateparse)
    df_meets['meet_start_date'] = pd.to_datetime(
        df_meets['meet_start_date'],
        format=form, errors='ignore', unit='s').dt.tz_localize('UTC')
    """
    global parsing_results

    io_data = StringIO(str(remote_data, 'utf-8'))
    # pd.to_datetime(t, format=form)
    # datetime_object = datetime.strptime(t, form)

    def dateparse(entry):
        try:
            return datetime.datetime.strptime(entry, settings.DATA_TIME_FORMAT)
        except Exception as err:
            pass
        return entry

    df = pd.read_csv(
        io_data,
        sep=';',
        header=None,
        names=['c1', 'c2', 'c3', 'c4'],
        # parse_dates=['c2', 'c3'], date_parser=dateparse,
        skip_blank_lines=False, # to log not parsed lines to DB (even empty)
        engine='python')

    # df_meets
    df_meets = df[df['c3'].notnull()].dropna(how='all', axis=1).copy()
    df_meets = df_meets.rename(
        columns={'c1': 'user_id', 'c2': 'meet_start_date',
                 'c3': 'meet_end_date', 'c4': 'meet_id'})

    # Use precise datetime parsing to keep contarct with remote data
    df_users = df[df['c3'].isnull()].dropna(how='all', axis=1).copy()
    df_users = df_users.rename(columns={'c1': 'user_id', 'c2': 'user_name'})

    total_rows_count=len(df.index) # 10224
    meets_rows_count=len(df_meets.index) # 10078
    users_rows_count=len(df_users.index) # 146

    pandas_kwargs = dict(
        total_rows=total_rows_count,
        meets_rows=meets_rows_count,
        users_rows=users_rows_count)

    if sum([meets_rows_count, users_rows_count]) != total_rows_count:
        raise (f'Pandas initial dataframes parsing error due to diff count '
               f'of rows: {pandas_kwargs}')
    parsing_results.update(pandas_kwargs)

    return df_users, df_meets

def is_new_data_for_sync(session, forced, sync_type):
    global last_sync, actual_sync, req, resp, errors

    req = Request(settings.SYNC_DATA_URL)
    actual_sync = Sync(
        start_date=datetime.datetime.now(),
        status=SyncStatus.started,
        type=sync_type,
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
        if not forced:
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
                errors=[error_msg],
                parsing_results={'sync_id': actual_sync.id}
            ))

            # Skip due to not modified 304 status code (no new content)
            if type(err) == HTTPError and err.status == 304:
                actual_sync_kwargs.update(**dict(
                    status=SyncStatus.skipped,
                    end_reason=SyncEndReason.no_new_remote_data))
                logging.warning(error_msg)

            else:
                # e.g. <urlopen error [Errno 111] Connection refused>
                actual_sync_kwargs.update(**dict(
                    status=SyncStatus.errors,
                    end_reason=SyncEndReason.remote_server_errors))
                logging.error(error_msg)
                # raise err

            py_utils.set_obj_attr_values(actual_sync, actual_sync_kwargs)
            session.commit()

            return False

    session.commit()

    return True


def get_remote_data(session, forced, sync_type):
    global last_sync, actual_sync, req, resp, errors, parsing_results

    if is_new_data_for_sync(session, forced, sync_type):
        parsing_results.update({
            'sync_id': actual_sync.id,
            'sync_type': sync_type,
        })
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
                end_reason=SyncEndReason.remote_server_errors,
                parsing_results=parsing_results,
            ))
            py_utils.set_obj_attr_values(actual_sync, actual_sync_kwargs)
            py_utils.update_obj_attr_values(
                actual_sync, dict(errors=[error_msg]))
            session.commit()

    return


def setup_db():
    db_session.init_sql(settings.DB_CONNECTION)


if __name__ == '__main__':
    run()