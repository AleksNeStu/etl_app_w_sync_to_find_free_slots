import json
import os
import sys
from importlib import import_module
from inspect import isclass
from pkgutil import iter_modules
from typing import Iterable


class DictToObj(dict):
    def __init__(self, *args, default_val='', **kwargs):
        self.default_val = default_val
        super().__init__(*args, **kwargs)

    def __getattr__(self, key):
        return self.get(key, self.default_val)


def import_modules(file, name, w_classes=True):
    # Iterate through the modules in the current package
    imported_modules = {}
    imported_classes = {}

    package_dir = os.path.dirname(file)
    for (_, module_name, _) in iter_modules([package_dir]):

        # Import the module and iterate through its attributes
        module = import_module(f"{name}.{module_name}")
        imported_modules[module_name] = module

        if w_classes:
            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)
                if isclass(attribute):
                    # Add the class to this package's variables
                    globals()[attribute_name] = attribute
                    imported_classes[attribute_name] = attribute

    return imported_modules, imported_classes


def add_module_do_sys_path(file, dir_path_part):
    directory = os.path.abspath(
        os.path.join(os.path.dirname(file), *dir_path_part))
    sys.path.insert(0, directory)


def is_json_str(data_str):
    try:
        json.loads(data_str)
    except Exception:
        return False

    return True


def is_json_obj(data_obj):
    try:
        json.dumps(data_obj)
    except Exception:
        return False

    return True

def is_json(data):
    return is_json_str(data) or is_json_obj(data)

def set_obj_attr_values(obj, obj_attrs_map, attr_names=None, is_db=True):
    # Skip no relevant to update cases w/ errors handling.
    # obj_attrs_map can contain e.g. list w/o json.dumps
    attr_names = attr_names or obj_attrs_map.keys()

    for attr_name in attr_names:
        attr_val = obj_attrs_map.get(attr_name)

        if is_db:
            # JSON flow.
            if is_json(attr_val):
                # Actualize final attr value.
                attr_val = (
                    json.dumps(attr_val)
                    if is_json_obj(attr_val) and not isinstance(attr_val, str) else attr_val)
                setattr(obj, attr_name, attr_val)
                continue

        # STR flow.
        setattr(obj, attr_name, attr_val)


#TODO: Add check existing values during updates, to avoud duplications.
def update_obj_attr_values(obj, obj_attrs_map, attr_names=None, is_db=True):
    # Skip no relevant to update cases w/ errors handling.
    # obj_attrs_map can contain e.g. list w/o json.dumps
    attr_names = attr_names or obj_attrs_map.keys()

    for attr_name in attr_names:
        act_val = getattr(obj, attr_name)
        new_val = obj_attrs_map.get(attr_name)

        # e.g. getting SA ORM obj isnt from DB def val is None, from Python
        # code is class default like {}.
        if act_val is not None:
            attr_val = None
            if all(isinstance(v, str) for v in [act_val, new_val]):
                attr_val = ', '.join([act_val, new_val])

            if is_db:
                # JSON flow.
                if is_json(act_val):
                    act_val = (
                        json.loads(act_val)
                        if is_json_str(act_val) else act_val)

                    # Update values.
                    if all(isinstance(v, dict)
                           for v in [act_val, new_val]):
                        act_val.update(new_val)
                    elif all(isinstance(v, list)
                             for v in [act_val, new_val]):
                        act_val.extend(new_val)
                    elif all(isinstance(v, (int, bool, float))
                             for v in [act_val, new_val]):
                        act_val = new_val

                    # Actualize final attr value.
                    attr_val = json.dumps(act_val)
                    setattr(obj, attr_name, attr_val)
                    continue

            # STR flow.
            setattr(obj, attr_name, attr_val)


def to_bool(txt):
    # 1, True, 0, False
    try:
        return bool(eval(txt))
    except Exception:
        pass

    return


def flatten(items):
    """Yield items from any nested iterable."""
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            for sub_x in flatten(x):
                yield sub_x
        else:
            yield x