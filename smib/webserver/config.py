from smib.common.config import *

WEBSERVER_SCHEME = config('WEBSERVER_SCHEME', default='http')
WEBSERVER_HOST = config('WEBSERVER_HOST', default='0.0.0.0')
WEBSERVER_PORT = config('WEBSERVER_PORT', default=80, cast=int)
WEBSERVER_PATH = config('WEBSERVER_PATH', default='', cast=to_path)
WEBSERVER_URL = urlparse(f"{WEBSERVER_SCHEME}://{WEBSERVER_HOST}:{WEBSERVER_PORT}/{WEBSERVER_PATH}")
WEBSERVER_SECRET_KEY = config('WEBSERVER_SECRET_KEY', default=os.urandom(24))
WEBSERVER_PATH_PREFIX = config('WEBSERVER_PATH_PREFIX', default='/smib')
WEBSERVER_TEMPLATES_DIRECTORY = config('WEBSERVER_TEMPLATES_DIRECTORY', default=ROOT_DIRECTORY / 'webserver' / 'templates', cast=Path)
WEBSERVER_STATIC_DIRECTORY = config('WEBSERVER_STATIC_DIRECTORY', default=ROOT_DIRECTORY / 'webserver' / 'static', cast=Path)
