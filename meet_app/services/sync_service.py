from typing import Optional

import sqlalchemy.orm as orm

from data import db_session
from data.models.syncs import Sync
from enums.sa import SyncStatus


def get_syncs(session: orm.Session = None) -> orm.Query:
    if session:
        return session.query(Sync)

    with db_session.create_session() as session:
        return session.query(Sync)


def get_latest_finished_sync(session: orm.Session = None,
                             syncs: orm.Query = None) -> Optional[Sync]:
    syncs = syncs or get_syncs(session)
    res = syncs.filter(Sync.status == SyncStatus.finished).order_by(
        Sync.id.desc()).first()
    # syncs.session.close()

    return res