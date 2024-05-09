from smib.common.config import *

SLACK_APP_TOKEN = config('SLACK_APP_TOKEN')
SLACK_BOT_TOKEN = config('SLACK_BOT_TOKEN')

WEBSOCKET_ALLOWED_HOSTS = config('WEBSOCKET_ALLOWED_HOSTS', default='localhost,127.0.0.1,::1', cast=Csv())

MONGO_DB_HOST = config('MONGO_DB_HOST', default='localhost')
MONGO_DB_PORT = config('MONGO_DB_PORT', default=27017, cast=int)

MONGO_DB_DEFAULT_DB = config("MONGO_DB_DEFAULT_DB", default="smib_default")
MONGO_DB_CONNECT_TIMEOUT_SECONDS = config("MONGO_DB_CONNECT_TIMEOUT_SECONDS", default=5, cast=int)

MONGO_DB_URL = f"mongodb://{MONGO_DB_HOST}:{MONGO_DB_PORT}/"

PLUGINS_DIRECTORY = config('PLUGINS_DIRECTORY', default=ROOT_DIRECTORY / 'slack' / 'plugins', cast=Path)

SPACE_OPEN_ANNOUNCE_CHANNEL_ID = config('SPACE_OPEN_ANNOUNCE_CHANNEL_ID', default='C06UDPLQRP1')