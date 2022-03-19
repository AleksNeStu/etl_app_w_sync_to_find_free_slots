import datetime
from dataclasses import dataclass

import sqlalchemy as sa
import sqlalchemy.orm as orm

from data.models.modelbase import SqlAlchemyBase


@dataclass
class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id: int = sa.Column(sa.BigInteger, primary_key=True, autoincrement=True)

    # Hash of unique user, calculated by 3rd party service
    hash_id: str = sa.Column(
        sa.String, nullable=False, unique=True, index=True)

    sync_id: int = sa.Column(
        sa.BigInteger, sa.ForeignKey('syncs.id'), nullable=False, index=True)

    # 1st amd 2nd user name, from 3rd party service (duplication are possible,
    # cause supposed 3rd party service generated it based on additional info)
    name: str = sa.Column(sa.String, nullable=False, index=True)

    created_date: datetime.datetime = sa.Column(
        sa.DateTime, default=datetime.datetime.now)
    updated_date: datetime.datetime = sa.Column(sa.DateTime, nullable=True)

    sync = orm.relationship('Sync')
