import flask
import werkzeug

from enums.sa import SyncType
from infra.request_mod import request_data
from infra.response_mod import response
from services import sync_service
from utils import py as py_utils
from bin import load_data


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


@blueprint.route('/', methods=['GET'])
@response()
@blueprint.errorhandler(werkzeug.exceptions.BadRequest)
def get_meta_info():
    return flask.jsonify([{
        'a1': 1,
        'a2': 2,
    }])