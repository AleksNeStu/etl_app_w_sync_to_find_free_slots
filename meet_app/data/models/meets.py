import datetime
from dataclasses import dataclass

import sqlalchemy as sa
import sqlalchemy.orm as orm
from timeslot import Timeslot
from data.models.modelbase import SqlAlchemyBase, UniqueMixin


@dataclass
class Meet(UniqueMixin, SqlAlchemyBase):
    __tablename__ = 'meets'

    id: int = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    # Hash of unique meet (most probably based on :
    # user_id, meet_start_dat, meet_end_date), calculated by 3rd party service
    hash_id: str = sa.Column(
        sa.String, nullable=False, unique=True, index=True)

    sync_id: int = sa.Column(
        sa.Integer, sa.ForeignKey('syncs.id'), nullable=False, index=True)

    user_id: int = sa.Column(
        sa.Integer, sa.ForeignKey('users.id'), nullable=False, index=True)

    # delta (start_date with end_date) duplications are possible
    start_date: datetime.datetime = sa.Column(
        sa.DateTime, nullable=False, index=True)
    end_date: datetime.datetime = sa.Column(
        sa.DateTime, nullable=False, index=True)

    created_date: datetime.datetime = sa.Column(
        sa.DateTime, default=datetime.datetime.utcnow)
    updated_date: datetime.datetime = sa.Column(sa.DateTime, nullable=True)

    sync = orm.relationship('Sync')

    @classmethod
    def unique_hash(cls, hash_id):
        return hash_id

    @classmethod
    def unique_filter(cls, query, hash_id):
        return query.filter(Meet.hash_id == hash_id)

    @property
    def timeslot(self):
        timeslot = Timeslot(self.start_date, self.end_date)
        return timeslot