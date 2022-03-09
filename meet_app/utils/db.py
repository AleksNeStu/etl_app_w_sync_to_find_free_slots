import hashlib

from passlib.handlers.sha2_crypt import sha512_crypt as crypto


def get_sql_lite_conn_str(db_file: str):
    db_file_stripped = db_file.strip()
    if not db_file or not db_file_stripped:
        # db_file = '../db/meet_app.db'
        raise Exception("SQL lite DB file is not specified.")

    return 'sqlite:///' + db_file_stripped


def to_hash(list_of_str) -> str:
    # |arg1|arg2|...|
    str_patern = '|{}|'.format('|'.join([str(s) for s in list_of_str]))
    return hashlib.sha512(str_patern.encode('utf-8')).hexdigest()