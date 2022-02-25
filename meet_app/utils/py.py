import os
import sys
from importlib import import_module
from inspect import isclass
from pkgutil import iter_modules


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


# TODO: make attr_names with processors funcs to calc specific values
def set_obj_attr_values(obj, obj_attrs_map, attr_names):
    for attr_name in attr_names:
        setattr(obj, attr_name, obj_attrs_map.get(attr_name))