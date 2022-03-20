"""Flask application run."""
import logging
import os
import sys

import flask
import pytz
import werkzeug
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from enums.sa import SyncStatus, SyncEndReason, NotSyncedItemReason, SyncType

import settings
from bin import load_data
from bin import run_migrations
from data import db_session
from infra.request_mod import request_data
from infra.response_mod import response
from migrations import utils as migrations_utils
from services import sync_service
from utils import py as py_utils

app = flask.Flask(__name__)
app.deploying = bool(int(os.getenv('IS_DEPLOY', '0')))
app.is_sql_ver = bool(int(os.getenv('IS_SQL_VERSION', '0')))


scheduler = BackgroundScheduler()

def main():
    configure()

    if not app.testing and not app.deploying:
        app.run(debug=False, host='localhost')


def configure():
    init_logging()
    update_cfg()
    register_blueprints()
    setup_db()

    if app.is_sql_ver:
        all_db_models = generate_all_db_models()

    run_actions()


def register_blueprints():
    # TODO: Add register blueprints
    pass


def setup_db():
    if app.is_sql_ver:
        # TODO: Add MySQL version
        db_session.init_sql(settings.DB_CONNECTION)
        # enable for flask app not in debug mode to avoid auto apply
        run_migrations.run()
    else:
        # TODO: Add MongoDB version
        db_session.init_no_sql(**settings.NOSQL_DB_CONNECTION)
        pass


def generate_all_db_models():
    db_models = migrations_utils.get_models(os.path.join(
        os.path.dirname(__file__), 'data', 'generated_all_db_models.py'))

    return db_models


def run_actions():
    # Sync data on application run.
    sync = load_data.run(sync_type=SyncType.app_init.value, forced=False)
    scheduler.start()

#TODO: Fix duplication of db entiries
# Sync data by interval.
@scheduler.scheduled_job(
    IntervalTrigger(timezone=pytz.utc, **settings.SYNC_INTERVAL))
def load_data_job():
    load_data.run(sync_type=SyncType.scheduled.value)


def init_logging():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    # logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    # logging.getLogger("sqlalchemy.pool").setLevel(logging.DEBUG)


def update_cfg():
    global app
    # flask_cfg.from_pyfile('settings.py') # no needed 'flask.py'
    app.config.update({
        **settings.FLASK_ENV_CFG,
        **settings.FLASK_SEC_ENV_CFG,
    })

# Sync data manually.
# Example: http://localhost:5000/load_data?forced=1
# Accepted 1, 0, True, False as values for forced
# @app.route('/load_data/<int:forced>', methods=['GET']) - not flexible but quick
@app.route('/load_data', methods=['GET'])
@response()
@app.errorhandler(werkzeug.exceptions.BadRequest)
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


if __name__ in ('__main__', 'meet_app.app'):
    main()
