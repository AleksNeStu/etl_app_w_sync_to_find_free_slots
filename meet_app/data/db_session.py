import contextlib
import logging
import os
import ssl

import mongoengine
import sqlalchemy as sa
import sqlalchemy.engine as engine
import sqlalchemy.orm as orm
import sqlalchemy_utils as sa_utils
from sqlalchemy.orm import Session

import app
import settings
from data.models.modelbase import SqlAlchemyBase

app.is_sql_ver = bool(int(os.getenv('IS_SQL_VERSION', '0')))

# https://docs.sqlalchemy.org/en/14/orm/session_basics.html
__session = None
__engine = None


def init_no_sql(**conn):
    formed_conn_data = {
        'alias': 'core',
        'name': conn.get('MONGODB_DB'),
    }
    user = conn.get('MONGODB_USERNAME')
    password = conn.get('MONGODB_PASSWORD')

    if user or password:
        formed_conn_data.update({
            'username': user,
            'password': password,
            'host': conn.get('MONGODB_HOST'),
            'port': conn.get('MONGODB_PORT'),
            'ssl': conn.get('MONGODB_SSL'),
            'ssl_cert_reqs': ssl.CERT_NONE,
            'authentication_source': 'admin',
            'authentication_mechanism': 'SCRAM-SHA-1',

        })

    mongoengine.register_connection(**formed_conn_data)
    formed_conn_data['password'] = '***'
    logging.info("NoSQL DB connection: {}".format(formed_conn_data))


def init_sql(conn):
    global __session
    if __session:
        return

    # engine
    # debug sql queries
    # logger = logging.getLogger('sqlalchemy.engine')
    # logger.setLevel(logging.DEBUG)
    engine = sa.create_engine(conn, echo=True)

    db_url = engine.url
    logging.info(
        "Engine created w/ a connection string: '{}'".format(conn))
    # DB create (not required for SQLite)
    # TODO: avoid delete DB every time
    if not sa_utils.database_exists(db_url):
        sa_utils.create_database(db_url)
    # if sa_utils.database_exists(db_url):
    #     sa_utils.drop_database(db_url)
    # sa_utils.create_database(engine.url)

    # session
    global __engine
    __engine = engine
    __session = orm.sessionmaker(bind=engine)

    # noinspection PyUnresolvedReferences
    import data.models
    SqlAlchemyBase.metadata.create_all(engine)


#TODO: Add list of used sessions with state
def create_session() -> orm.Session:
    # With this configuration, each time we call our sessionmaker instance,
    # we get a new Session instance back each time.
    global __session

    if not __session and app.is_sql_ver:
        init_sql(settings.DB_CONNECTION)

    session: Session = __session()
    # views.account_views.register_post
    # sqlalchemy.orm.exc.DetachedInstanceError: Instance <User at 0x7f5dc0a5afe0> is not bound to a Session; attribute refresh operation cannot proceed (Background on this error at: https://sqlalche.me/e/14/bhk3)
    session.expire_on_commit = False

    return session


def create_engine() -> engine.Engine:
    global __engine

    if not __engine and app.is_sql_ver:
        init_sql(settings.DB_CONNECTION)

    return __engine


@contextlib.contextmanager
def expire_session(expire_on_commit=True):
    session = create_session()
    session.expire_on_commit = expire_on_commit
    try:
        yield session
    finally:
        session.expire_on_commit = True
        session.close()