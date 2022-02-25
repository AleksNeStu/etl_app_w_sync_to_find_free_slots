def get_sql_lite_conn_str(db_file: str):
    db_file_stripped = db_file.strip()
    if not db_file or not db_file_stripped:
        # db_file = '../db/meet_app.db'
        raise Exception("SQL lite DB file is not specified.")

    return 'sqlite:///' + db_file_stripped