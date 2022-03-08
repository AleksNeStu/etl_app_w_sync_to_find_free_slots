import enum

# To avoid {TypeError}Object of type xxx is not JSON serializable use mixin str
# https://stackoverflow.com/questions/24481852/serialising-an-enum-member-to-json
@enum.unique
class SyncStatus(str, enum.Enum):
    started: str = 'started'
    skipped: str = 'skipped'
    got_data: str = 'got_data'
    finished: str = 'finished' # meaning got data was parsed
    errors: str = 'errors'

@enum.unique
class SyncEndReason(str, enum.Enum):
    no_new_remote_data: str = 'no_new_remote_data'
    remote_server_errors: str = 'remote_server_errors'
    data_parsing_errors: str = 'data_parsing_errors'
    data_parsing_end: str = 'data_parsing_end'