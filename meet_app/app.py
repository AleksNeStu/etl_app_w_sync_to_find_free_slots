"""Flask application run."""
import logging
import os
import sys

import flask

import settings
from bin import load_data
from bin import run_migrations
from data import db_session
from infra.response_mod import response

app = flask.Flask(__name__)
app.deploying = bool(int(os.getenv('IS_DEPLOY', '0')))
app.is_sql_ver = bool(int(os.getenv('IS_SQL_VERSION', '0')))


def main():
    configure()

    if not app.testing and not app.deploying:
        app.run(debug=True, host='localhost')


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
        # TODO: Add scheduler (Python and(or) OS versions)
        load_data.run()
    else:
        # TODO: Add MongoDB version
        db_session.init_no_sql(**settings.NOSQL_DB_CONNECTION)
        pass


def generate_all_db_models():
    pass
    # TODO: Add generate all db models
    # from migrations import utils as migrations_utils
    # db_models = migrations_utils.get_models(os.path.join(
    #     os.path.dirname(__file__), 'data', 'generated_all_db_models.py'))
    # return db_models


def run_actions():
    # TODO: Add run actions
    pass


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

# TODO: Sync via Python and(or) cron
@app.route('/load_data')
@response()
def load_meet_data():
    return load_data.run()


if __name__ in ('__main__', 'meet_app.app'):
    main()
