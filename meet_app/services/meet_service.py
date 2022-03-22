from typing import Optional, List

import sqlalchemy.orm as orm

from data import db_session
from data.models.meets import Meet


def get_meets_qr(session: orm.Session = None) -> orm.Query:
    if session:
        return session.query(Meet)

    with db_session.create_session() as session:
        return session.query(Meet)


def get_meets_by_users_ids(users_ids: List[int], session: orm.Session = None,
                           meets: orm.Query = None) -> Optional[Meet]:
    meets = meets or get_meets_qr(session)
    res = meets.filter(Meet.user_id.in_(users_ids)).all()

    return res

def get_busy_timeslots_by_users_ids(users_ids: List[int]):
    users_meets = get_meets_by_users_ids(users_ids)
    meets_timeslots = [
        u_meet.timeslot for u_meet in users_meets
    ]
    return meets_timeslots
