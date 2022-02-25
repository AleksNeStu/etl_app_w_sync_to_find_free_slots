import datetime
import json

import sqlalchemy
import sqlalchemy as sa
from sqlalchemy.types import TypeDecorator

from data.models.modelbase import SqlAlchemyBase
from enums.sa import SyncStatus


class Sync(SqlAlchemyBase):
    __tablename__ = 'syncs'

    id: int = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    start_date: datetime.datetime = sa.Column(
        sa.DateTime, index=True, nullable=False)
    end_date: datetime.datetime = sa.Column(
        sa.DateTime, index=True)
    status: str = sa.Column(sa.Enum(SyncStatus), nullable=False)
    resp_headers = sa.Column(sa.JSON, default={})
    results = sa.Column(sa.JSON, default={})
    errors = sa.Column(sa.JSON, default={})