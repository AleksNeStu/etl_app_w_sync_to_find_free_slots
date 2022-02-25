import enum


class SyncStatus(enum.Enum):
    in_progress = 'in_progress'
    finished = 'finished'
    skipped = 'skipped'
    errors = 'errors'