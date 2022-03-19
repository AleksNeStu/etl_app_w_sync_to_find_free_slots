import datetime
import json
from dataclasses import dataclass

import sqlalchemy as sa

from data.models.modelbase import SqlAlchemyBase
from enums.sa import SyncStatus, SyncEndReason


@dataclass
class Sync(SqlAlchemyBase):
    __tablename__ = 'syncs'

    id: int = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    start_date: datetime.datetime = sa.Column(
        sa.DateTime, index=True, nullable=False)
    end_date: datetime.datetime = sa.Column(
        sa.DateTime, index=True)
    status: str = sa.Column(sa.Enum(SyncStatus), nullable=False)
    resp_headers: str = sa.Column(sa.JSON, default=json.dumps({}))
    parsing_results: str = sa.Column(sa.JSON, default=json.dumps({}))
    errors: str = sa.Column(sa.JSON, default=json.dumps([]))
    end_reason: str = sa.Column(sa.Enum(SyncEndReason))