import functools
import inspect
from pathlib import Path

from injectable import inject
from mogo import Model, Field, connect

from smib.slack.plugin import PluginManager
from smib.common.utils import get_module_file
from smib.common.config import MONGO_DB_URL, MONGO_DB_CONNECT_TIMEOUT_SECONDS


def get_current_plugin_id() -> str:
    plugin_manager: PluginManager = inject("PluginManager")
    plugin_name = plugin_manager.get_plugin_from_file(get_module_file(2)).id
    return plugin_name


def database(database_name: str = None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            db_name = database_name

            # If no database_name parameter name passed in, get current plugin id and use that
            if db_name is None:
                plugin_file = Path(inspect.getfile(inspect.unwrap(func)))
                plugin_manager: PluginManager = inject("PluginManager")
                db_name = plugin_manager.get_plugin_from_file(plugin_file).id

            inject("logger").debug(f"Database name: {db_name}")

            # Connect to DB and close it afterward
            with connect(db_name, uri=MONGO_DB_URL, timeoutMs=1000*MONGO_DB_CONNECT_TIMEOUT_SECONDS):
                return func(*args, **kwargs)

        return wrapper

    return decorator
