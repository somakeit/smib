import json
import logging.config
from urllib.parse import urlparse
from decouple import config, Csv
import warnings
import os
from pathlib import Path
import smib

from smib.common.utils import to_path

warnings.filterwarnings("ignore", category=RuntimeWarning)

ROOT_DIRECTORY = Path(smib.__file__).parent

APPLICATION_NAME = config('APPLICATION_NAME', default='S.M.I.B.')

SLACK_APP_TOKEN = config('SLACK_APP_TOKEN')
SLACK_BOT_TOKEN = config('SLACK_BOT_TOKEN')

WEBSERVER_SCHEME = config('WEBSERVER_SCHEME', default='http')
WEBSERVER_HOST = config('WEBSERVER_HOST', default='0.0.0.0')
WEBSERVER_PORT = config('WEBSERVER_PORT', default=80, cast=int)
WEBSERVER_PATH = config('WEBSERVER_PATH', default='', cast=to_path)
WEBSERVER_URL = config('WEBSOCKET_URL',
                       default=f"{WEBSERVER_SCHEME}://{WEBSERVER_HOST}:{WEBSERVER_PORT}/{WEBSERVER_PATH}",
                       cast=urlparse)
WEBSERVER_SECRET_KEY = config('WEBSERVER_SECRET_KEY', default=os.urandom(24))
WEBSERVER_PATH_PREFIX = config('WEBSERVER_PATH_PREFIX', default='/smib')
WEBSERVER_TEMPLATES_DIRECTORY = config('WEBSERVER_TEMPLATES_DIRECTORY', default=ROOT_DIRECTORY / 'webserver' / 'templates', cast=Path)
WEBSERVER_STATIC_DIRECTORY = config('WEBSERVER_STATIC_DIRECTORY', default=ROOT_DIRECTORY / 'webserver' / 'static', cast=Path)

WEBSOCKET_SCHEME = config('WEBSERVER_SCHEME', default='ws')
WEBSOCKET_HOST = config('WEBSOCKET_HOST', default='localhost')
WEBSOCKET_PORT = config('WEBSOCKET_PORT', default=4123, cast=int)
WEBSOCKET_PATH = config('WEBSOCKET_PATH', default='ws', cast=to_path)
WEBSOCKET_URL = config('WEBSOCKET_URL',
                       default=f"{WEBSOCKET_SCHEME}://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}/{WEBSOCKET_PATH}",
                       cast=urlparse)
WEBSOCKET_ALLOWED_HOSTS = config('WEBSOCKET_ALLOWED_HOSTS', default='localhost,127.0.0.1,::1', cast=Csv())

MONGO_DB_HOST = config('MONGO_DB_HOST', default='localhost')
MONGO_DB_PORT = config('MONGO_DB_PORT', default=27017, cast=int)

MONGO_DB_URL = f"mongodb://{MONGO_DB_HOST}:{MONGO_DB_PORT}/"

MONGO_DB_PLUGINS_USER = config('MONGO_DB_PLUGINS_USER', default='plugins')
MONGO_DB_PLUGINS_PASSWORD = config('MONGO_DB_PLUGINS_PASSWORD', default='plug1n5')

MONGO_DB_PLUGINS_NAME = config('MONGO_DB_PLUGINS_NAME', default='smib_plugins')

MONGO_DB_ADMIN_USER = config('MONGO_DB_ADMIN_USER')
MONGO_DB_ADMIN_PASSWORD = config('MONGO_DB_ADMIN_PASSWORD')

PLUGINS_DIRECTORY = config('PLUGINS_DIRECTORY', default=ROOT_DIRECTORY / 'slack' / 'plugins', cast=Path)

SPACE_OPEN_ANNOUNCE_CHANNEL_ID = config('SPACE_OPEN_ANNOUNCE_CHANNEL_ID', default='C06UDPLQRP1')
