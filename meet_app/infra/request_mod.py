from typing import Optional

import flask
from flask import Request
from werkzeug.datastructures import MultiDict, CombinedMultiDict

from utils.py import DictToObj


def request_data(req: Optional[Request] = None,
                 default_val='', **route_kwargs) -> DictToObj:
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

    return DictToObj(default_val=default_val, **data)