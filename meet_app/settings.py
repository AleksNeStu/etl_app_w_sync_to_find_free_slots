import os
from utils import db as db_utils
import dotenv

# APP
APP_ROOT_DIR = os.getenv('APP_ROOT_DIR', os.path.dirname(__file__))
PROJECT_ROOT_DIR = os.getenv(
    'PROJECT_ROOT_DIR', os.path.join(APP_ROOT_DIR, '../'))
ALEMBIC_INI = os.getenv(
    'ALEMBIC_INI', os.path.join(PROJECT_ROOT_DIR, 'alembic.ini'))
RUN_ACTIONS = bool(int(os.getenv('RUN_ACTIONS', '0')))
IS_DEPLOY = bool(int(os.getenv('IS_DEPLOY', '0')))
IS_SQL_VERSION = bool(int(os.getenv('IS_SQL_VERSION', '1')))

# ENV GLOBAL INIT
LOCAL_ENV_PATH = os.getenv(
    'LOCAL_ENV_PATH', os.path.join(PROJECT_ROOT_DIR, 'configs/local.env'))
FLASK_ENV_PATH = os.getenv(
    'FLASK_ENV_PATH', os.path.join(PROJECT_ROOT_DIR, 'configs/flask.env'))
FLASK_SEC_ENV_PATH = os.getenv(
    'FLASK_SEC_ENV_PATH', os.path.join(
        PROJECT_ROOT_DIR, 'configs/flask.env.sec'))
# LOCAL_ENV_CFG
# Get dict of vars from .env and set to LOCAL_ENV_PATH.py
LOCAL_ENV_CFG = dotenv.dotenv_values(LOCAL_ENV_PATH)
locals().update(LOCAL_ENV_CFG)
# for k, v in LOCAL_ENV_CFG.items():
#     exec(k + '=v')
# Make .env vars like os vars
dotenv.load_dotenv(LOCAL_ENV_PATH)

# FLASK_ENV_CFG
FLASK_ENV_CFG = dotenv.dotenv_values(FLASK_ENV_PATH)
FLASK_SEC_ENV_CFG = dotenv.dotenv_values(FLASK_SEC_ENV_PATH)

# DB
DB_NAME = os.getenv('DB_NAME', 'meet_app')
DB_MYSQL_CLIENT = os.getenv('DB_MYSQL_CLIENT', 'mysql+mysqldb')

# SQLite
DB_SQLITE_FILE_NAME = os.environ.get(
    'DB_SQLITE_FILE_NAME', '{}.db'.format(DB_NAME))
DB_SQLITE_FILE = os.environ.get('DB_SQLITE_FILE', os.path.join(
    APP_ROOT_DIR, 'db', DB_SQLITE_FILE_NAME))
DB_CONNECTION_SQLITE = os.environ.get(
    'DB_CONNECTION_SQLITE', db_utils.get_sql_lite_conn_str(DB_SQLITE_FILE))
# MySQL
DB_CONNECTION_MYSQL = os.environ.get(
    'DB_CONNECTION_MYSQL',
    '{}://root:rootroot@localhost/{}'.format(DB_MYSQL_CLIENT, DB_NAME))

# 1) Py2 (Default): https://pypi.org/project/MySQL-python/
# DB_CONNECTION_MYSQL = os.environ.get(
#     'DB_CONNECTION_MYSQL',
#     '{}://root:rootroot@localhost/{}'.format('mysql', DB_NAME))

# 2) mysqlclient (a maintained fork of MySQL-Python)
# # Py3: https://github.com/PyMySQL/mysqlclient
# DB_CONNECTION_MYSQL = os.environ.get(
#     'DB_CONNECTION_MYSQL',
#     '{}://root:rootroot@localhost/{}'.format('mysql+mysqldb', DB_NAME))

# 3) PyMySQL
# # https://github.com/PyMySQL/PyMySQL
# DB_CONNECTION_MYSQL = os.environ.get(
#     'DB_CONNECTION_MYSQL',
#     '{}://root:rootroot@localhost/{}'.format('mysql+pymysql', DB_NAME))
# Active DB connection
DB_CONNECTION = DB_CONNECTION_SQLITE

# SQLAlchemy
# InvalidRequestError: VARCHAR requires a length on dialect mysql
STR_LENGTH = os.environ.get('STR_LENGTH', 255)

# No SQL
# 1) MongoDB
NO_SQL_ENV_PATH = os.getenv(
    'NO_SQL_ENV_PATH', os.path.join(
        PROJECT_ROOT_DIR, 'configs/no_sql.env'))
NOSQL_DB_CONNECTION = dotenv.dotenv_values(NO_SQL_ENV_PATH)
# TODO: If IS_DEPLOY=1 update NOSQL_DB_CONNECTION by {MONGODB_USERNAME: ..., MONGODB_PASSWORD: ...}


# Meet app
SYNC_DATA_URL = ('https://builds.lundalogik.com/api/v1/'
                 'builds/freebusy/versions/1.0.0/file')
