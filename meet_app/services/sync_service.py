from typing import Optional

import sqlalchemy.orm as orm
from sqlalchemy import and_

from data import db_session
from data.models.syncs import Sync
from enums.sa import SyncStatus
from utils import py as py_utils


def get_syncs_qr(session: orm.Session = None) -> orm.Query:
    if session:
        return session.query(Sync)

    with db_session.create_session() as session:
        return session.query(Sync)


def get_latest_finished_sync(session: orm.Session = None,
                             syncs_qr: orm.Query = None) -> Optional[Sync]:
    syncs_qr = syncs_qr or get_syncs_qr(session)
    res = syncs_qr.filter(Sync.status == SyncStatus.finished).order_by(
        Sync.id.desc()).first()
    # syncs.session.close()

    return res

def get_latest_sync(session: orm.Session = None,
                    syncs_qr: orm.Query = None) -> Optional[Sync]:
    syncs_qr = syncs_qr or get_syncs_qr(session)
    res = syncs_qr.order_by(Sync.id.desc()).first()
    # syncs.session.close()

    return res


def get_sync(get_kwargs: dict, session: orm.Session = None,
             syncs_qr: orm.Query = None) -> Optional[Sync]:
    syncs_qr = syncs_qr or get_syncs_qr(session)
    _and = [getattr(Sync, k) == v for k, v in get_kwargs.items()]
    res = syncs_qr.filter(and_(*_and)).order_by(Sync.id.desc()).first()

    return res


def update_sync(update_kwargs: dict,
                get_kwargs: dict = None,
                sync: Sync = None,
                session: orm.Session = None) -> Optional[Sync]:
    sync = sync or get_sync(get_kwargs, session)

    py_utils.update_obj_attr_values(sync, update_kwargs)
    session.commit()