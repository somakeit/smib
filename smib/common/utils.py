import functools
import pickle
import traceback
from pathlib import Path


def is_pickleable(obj):
    try:
        pickle.dumps(obj)
        return True
    except (pickle.PicklingError, AttributeError, TypeError):
        return False


def to_path(x):
    path = Path(f"/{x.lstrip('/')}").as_posix().lstrip('/')
    return path


def log_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f'{e.__class__.__name__}: {e}')
    return wrapper


def singleton(class_):
    instances = {}
    def wrapper(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return wrapper
