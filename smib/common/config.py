from urllib.parse import urlparse
from decouple import config, Csv
import warnings
import os

from smib.common.utils import to_path

warnings.filterwarnings("ignore", category=RuntimeWarning)

SLACK_APP_TOKEN = config('SLACK_APP_TOKEN')
SLACK_BOT_TOKEN = config('SLACK_BOT_TOKEN')

WEBSERVER_SCHEME = config('WEBSERVER_SCHEME', default='http')
WEBSERVER_HOST = config('WEBSERVER_HOST', default='0.0.0.0')
WEBSERVER_PORT = config('WEBSERVER_PORT', default=80, cast=int)
WEBSERVER_PATH = config('WEBSOCKET_PATH', default='', cast=to_path)
WEBSERVER_URL = config('WEBSOCKET_URL',
                       default=f"{WEBSERVER_SCHEME}://{WEBSERVER_HOST}:{WEBSERVER_PORT}/{WEBSERVER_PATH}",
                       cast=urlparse)
WEBSERVER_SECRET_KEY = config('WEBSERVER_SECRET_KEY', default=os.urandom(24))

WEBSOCKET_SCHEME = config('WEBSERVER_SCHEME', default='ws')
WEBSOCKET_HOST = config('WEBSOCKET_HOST', default='localhost')
WEBSOCKET_PORT = config('WEBSOCKET_PORT', default=5000, cast=int)
WEBSOCKET_PATH = config('WEBSOCKET_PATH', default='ws', cast=to_path)
WEBSOCKET_URL = config('WEBSOCKET_URL',
                       default=f"{WEBSOCKET_SCHEME}://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}/{WEBSOCKET_PATH}",
                       cast=urlparse)
WEBSOCKET_ALLOWED_HOSTS = config('WEBSOCKET_ALLOWED_HOSTS', default='localhost,127.0.0.1,::1', cast=Csv())
