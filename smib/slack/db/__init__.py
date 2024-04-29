import logging
from functools import partial
from logging import Logger

import pymongo.errors
from injectable import injectable_factory, inject, load_injection_container
from mogo import Model, Field, connect
from pymongo import MongoClient

from slack.plugin import PluginManager
from smib.common.utils import _get_module_name, _get_module_file
from smib.common.config import MONGO_DB_URL, MONGO_DB_ADMIN_PASSWORD, MONGO_DB_ADMIN_USER


def connect_to_plugin_database(plugin_id: str):
    return connect(plugin_id, uri=MONGO_DB_URL)


def get_plugin_database():
    plugin_manager: PluginManager = inject("PluginManager")
    plugin_name = plugin_manager.get_plugin_from_file(_get_module_file(2)).id
    return connect_to_plugin_database(plugin_name)


@injectable_factory(Logger, qualifier="logger")
def logger_factory():
    return logging.getLogger(__name__)
