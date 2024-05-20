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

WEBSOCKET_SCHEME = config('WEBSERVER_SCHEME', default='ws')
WEBSOCKET_HOST = config('WEBSOCKET_HOST', default='localhost')
WEBSOCKET_PORT = config('WEBSOCKET_PORT', default=4123, cast=int)
WEBSOCKET_PATH = config('WEBSOCKET_PATH', default='ws', cast=to_path)
WEBSOCKET_URL = urlparse(f"{WEBSOCKET_SCHEME}://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}/{WEBSOCKET_PATH}")

EXTERNAL_CONFIG_LOCATION = config('_EXTERNAL_CONFIG_LOCATION', default='/app/config/', cast=Path)
