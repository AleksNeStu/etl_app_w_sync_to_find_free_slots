import flask
import werkzeug

from bin import load_data
from enums.sa import SyncType
from infra import time_slots
from infra.request_mod import request_data
from infra.response_mod import response
from services import sync_service
from utils import py as py_utils
from timeslot import Timeslot


blueprint = flask.Blueprint('meet', __name__, template_folder='templates')


# Sync data manually.
# Example: http://localhost:5000/load_data?forced=1
# Accepted 1, 0, True, False as values for forced
# @app.route('/load_data/<int:forced>', methods=['GET']) - not flexible but quick
@blueprint.route('/load_data', methods=['GET'])
@response()
@blueprint.errorhandler(werkzeug.exceptions.BadRequest)
def load_meet_data():
    req_data = request_data(flask.request)

    forced = py_utils.to_bool(req_data.forced) if req_data.forced else False
    if forced is None:
        return 'Bad request to load data', 400

    sync_type = (
        SyncType.manual_forced.value if forced else SyncType.manual.value)
    sync = load_data.run(sync_type=sync_type, forced=forced)
    # Get actual sync status from DB based on sync id.
    db_actual_sync = sync_service.get_sync(get_kwargs={'id': sync.id})
    return flask.jsonify(db_actual_sync)


@blueprint.route('/get_free_slots', methods=['GET'])
@response()
@blueprint.errorhandler(werkzeug.exceptions.BadRequest)
def get_free_slots():
    req_data = request_data(flask.request)

    if req_data is None:
        return 'Bad request to get free slots', 400


    search_slot = Timeslot(req_data.start_date, req_data.end_date)
    free_slots_kwargs = dict(
        users_ids=req_data.users_ids,
        exp_slot=search_slot,
        exp_meet_len=req_data.meet_len,
        exp_working_hours=py_utils.WorkingHours(
            req_data.start_work, req_data.end_work)
    )

    busy_slots, free_slots = time_slots.get_free_slots(**free_slots_kwargs)
    free_slots_repr = [str(free_slot) for free_slot in free_slots]

    b_min_slot, b_max_slot, b_joined_slot = time_slots.get_joined_slot(
        busy_slots)
    f_min_slot, f_max_slot, _ = time_slots.get_joined_slot(free_slots)
    overlapped_w_busy_slots = search_slot.intersects(b_joined_slot)

    free_slots_resp = {
        'busy_slots_meta': {
            'min': str(b_min_slot),
            'max': str(b_max_slot),
            'count': len(busy_slots)
        },
        'free_slots_meta': {
            'min': str(f_min_slot),
            'max': str(f_max_slot),
            'count': len(free_slots)
        },
        'search_params': str(free_slots_kwargs),
        'overlapped_w_busy_slots': overlapped_w_busy_slots,
        'free_slots': free_slots_repr,
    }

    return flask.jsonify(free_slots_resp)


@blueprint.route('/', methods=['GET'])
@response()
@blueprint.errorhandler(werkzeug.exceptions.BadRequest)
def get_meta_info():
    return flask.jsonify([{
        'app': 'Application to get suggestions for suitable meeting times',
        'url_sync_data': 'http://localhost:5000/load_data',
        'url_sync_data_force': 'http://localhost:5000/load_data?forced=1',
        'url_get_free_slots': 'http://localhost:5000/get_free_slots',
    }])