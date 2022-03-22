from datetime import timedelta
from typing import Optional

import flask
from flask import Request
from werkzeug.datastructures import MultiDict, CombinedMultiDict

from utils import py as py_utils


def convert_get_slots_data(data):
    # Convertor of get free slots: '/get_free_slots'
    # users_ids:1,7,13
    # start_date:2012-05-21T06:00:00
    # end_date:2012-05-23T20:00:00
    # meet_len:30
    # start_work:08:30:00
    # end_work:17:30:00
    get_slots_data = {}
    try:
        get_slots_data['users_ids'] = [
            int(u_id) for u_id in data['users_ids'].split(',')]
        get_slots_data['start_date'] = py_utils.parse_req_dt(
            data['start_date'])
        get_slots_data['end_date'] = py_utils.parse_req_dt(
            data['end_date'])
        get_slots_data['meet_len'] = timedelta(minutes=int(data['meet_len']))
        get_slots_data['start_work'] = py_utils.parse_req_t(
            data['start_work'])
        get_slots_data['end_work'] = py_utils.parse_req_t(
            data['end_work'])
    except Exception:
        return

    if None in get_slots_data.values():
        return
    # Convertor of get free slots: '/get_free_slots'
    return data.update(get_slots_data)


def request_data(req: Optional[Request] = None,
                 default_val='',
                 **route_kwargs) -> Optional[py_utils.DictToObj]:
    req = req or flask.request
    data_src = [req.args, req.headers, req.cookies, req.form, route_kwargs]
    # args:  The key/value pairs in the URL query string
    # headers: Header items
    # cookies: Cookies items
    # form: The key/value pairs from the body, from a HTML post form

    data = {}
    for d_src in data_src:
        if isinstance(d_src, (MultiDict, CombinedMultiDict)):
            d_src = d_src.to_dict()
        data.update(d_src)

    if req.path == '/get_free_slots':
        convert_get_slots_data(data)

    return py_utils.DictToObj(default_val=default_val, **data)