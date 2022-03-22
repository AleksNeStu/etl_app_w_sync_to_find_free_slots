from typing import Optional, List

import sqlalchemy.orm as orm
from sqlalchemy import and_

from data import db_session
from data.models.users import User


def get_users_qr(session: orm.Session = None) -> orm.Query:
    if session:
        return session.query(User)

    with db_session.create_session() as session:
        return session.query(User)


def get_user(get_kwargs: dict, session: orm.Session = None,
             users: orm.Query = None) -> Optional[User]:
    users = users or get_users_qr(session)
    _and = [getattr(User, k) == v for k, v in get_kwargs.items()]
    res = users.filter(and_(*_and)).order_by(User.id.desc()).first()

    return res

def get_users_by_ids(ids: List[int], session: orm.Session = None,
                     users: orm.Query = None) -> Optional[User]:
    users = users or get_users_qr(session)
    res = users.filter(User.id.in_(ids)).all()

    return res


def get_user_hash_id(user_hash_id: str,
                     users_qr: orm.Query = None) -> Optional[User]:
    users_qr = users_qr or get_users_qr()
    user = users_qr.filter(User.hash_id == user_hash_id).first()
    # users_qr.session.close()

    return user