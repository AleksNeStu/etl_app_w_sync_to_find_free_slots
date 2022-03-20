import datetime
from dataclasses import dataclass

import sqlalchemy as sa
import sqlalchemy.orm as orm

from data.models.modelbase import SqlAlchemyBase, UniqueMixin


@dataclass
class User(UniqueMixin, SqlAlchemyBase):
    __tablename__ = 'users'

    id: int = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    # Hash of unique user, calculated by 3rd party service
    hash_id: str = sa.Column(
        sa.String, nullable=False, unique=True, index=True)

    sync_id: int = sa.Column(
        sa.Integer, sa.ForeignKey('syncs.id'), nullable=False, index=True)

    # 1st amd 2nd user name, from 3rd party service (duplication are possible,
    # cause supposed 3rd party service generated it based on additional info)
    name: str = sa.Column(sa.String, nullable=False, index=True)

    created_date: datetime.datetime = sa.Column(
        sa.DateTime, default=datetime.datetime.utcnow)
    updated_date: datetime.datetime = sa.Column(sa.DateTime, nullable=True)

    sync = orm.relationship('Sync')

    @classmethod
    def unique_hash(cls, hash_id):
        return hash_id

    @classmethod
    def unique_filter(cls, query, hash_id):
        return query.filter(User.hash_id == hash_id)
