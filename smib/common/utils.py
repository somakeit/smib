import importlib
import inspect
import logging
import pickle
import datetime
from pathlib import Path

import functools
import json

from injectable import inject
from slack_bolt.response import BoltResponse
from importlib.metadata import version

def is_pickleable(obj):
    try:
        pickle.dumps(obj)
        return True
    except (pickle.PicklingError, AttributeError, TypeError):
        return False

def is_json_encodable(value):
    try:
        json.dumps(value)
        return True
    except TypeError:
        return False


def to_path(x):
    path = Path(f"/{x.lstrip('/')}").as_posix().lstrip('/')
    return path


def log_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger: logging.Logger = inject("logger")
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f'{e.__class__.__name__}: {e}')

    return wrapper


def singleton(class_):
    instances = {}

    def wrapper(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return wrapper


def http_bolt_response(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)

        # Return raw BoltResponse object
        if isinstance(response, BoltResponse):
            return response

        # Return BoltResponse with body as json if return value is a dict
        if isinstance(response, dict):
            return BoltResponse(status=200, body=json.dumps(response))

        # Return bolt response with specified status code and json body
        # used with: return 200, {"ok": True}
        if type(response) in (list, tuple):
            if len(response) == 2 and isinstance(response[0], int) and isinstance(response[1], dict):
                return BoltResponse(status=response[0], body=json.dumps(response[1]))

    return wrapper


def get_module_name(stack_num: int = 4):
    stack = inspect.stack()
    frame = stack[stack_num]
    module = inspect.getmodule(frame[0])
    module_name = module.__name__
    return module_name


def get_module_file(stack_num: int = 4) -> Path:
    stack = inspect.stack()
    frame = stack[stack_num]
    file = inspect.getfile(frame[0])
    return Path(file)


def get_version() -> str:
    from smib.common.config import ROOT_DIRECTORY

    try:
        package_name = __package__.split('.')[0]
    except AttributeError:
        package_name = ROOT_DIRECTORY.parts[-1]

    return version(package_name)


def get_utc_datetime() -> datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc)


if __name__ == '__main__':
    print(f"{get_version() = }")

