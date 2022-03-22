"""Flask application run."""
import logging
import os
import sys

import flask
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

import settings
from bin import load_data
from bin import run_migrations
from data import db_session
from enums.sa import SyncType
from migrations import utils as migrations_utils

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
    from views import sync_views

    app.register_blueprint(sync_views.blueprint)
    # from utils import py as py_utils
    # views, _ = py_utils.import_modules(
    #     'views/__init__.py', 'views', w_classes=False)
    # for view in views.values():
    #     app.register_blueprint(view.blueprint)


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


if __name__ in ('__main__', 'meet_app.app'):
    main()
