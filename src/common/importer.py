# https://github.com/encode/uvicorn/blob/a50051308509600388ed170fdedacfb673757de4/uvicorn/importer.py#L9
import importlib
from typing import Any


class ImportFromStringError(Exception):
    pass


def import_from_string(import_str: Any) -> Any:
    if not isinstance(import_str, str):
        return import_str

    module_str, _, attrs_str = import_str.partition(":")
    if not module_str or not attrs_str:
        message = 'Import string "{import_str}" must be in format "<module>:<attribute>".'
        raise ImportFromStringError(message.format(import_str=import_str))

    try:
        module = importlib.import_module(module_str)
    except ModuleNotFoundError as exc:
        if exc.name != module_str:
            raise exc from None
        message = 'Could not import module "{module_str}".'
        raise ImportFromStringError(message.format(module_str=module_str))

    instance = module
    try:
        for attr_str in attrs_str.split("."):
            instance = getattr(instance, attr_str)
    except AttributeError:
        message = 'Attribute "{attrs_str}" not found in module "{module_str}".'
        raise ImportFromStringError(message.format(attrs_str=attrs_str, module_str=module_str))

    return instance


def resolve(s):
    """
    https://github.com/python/cpython/blob/46006a1b355f75d06c10e7b8086912c483b34487/Lib/logging/config.py#L393
    Resolve strings to objects using standard import and attribute
    syntax.
    """
    importer = staticmethod(__import__)
    name = s.split(".")
    used = name.pop(0)
    try:
        found = importer(used)
        for frag in name:
            used += "." + frag
            try:
                found = getattr(found, frag)
            except AttributeError:
                importer(used)
                found = getattr(found, frag)
        return found
    except ImportError as e:
        v = ValueError("Cannot resolve %r: %s" % (s, e))
        raise v from e


def _resolve(name):
    """
    https://github.com/python/cpython/blob/46006a1b355f75d06c10e7b8086912c483b34487/Lib/logging/config.py#L94C1-L106C17
    Resolve a dotted name to a global object.
    """
    name = name.split(".")
    used = name.pop(0)
    found = __import__(used)
    for n in name:
        used = used + "." + n
        try:
            found = getattr(found, n)
        except AttributeError:
            __import__(used)
            found = getattr(found, n)
    return found
