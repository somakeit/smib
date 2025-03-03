from pathlib import Path
from decouple import config
from smib.utilities.package import get_package_root, get_package_version

PACKAGE_NAME: str = "smib"
PACKAGE_DISPLAY_NAME: str = "S.M.I.B."
PACKAGE_DESCRIPTION: str = "The SoMakeIt Bot."

PACKAGE_VERSION: str = get_package_version(PACKAGE_NAME)

PACKAGE_ROOT: Path = get_package_root(PACKAGE_NAME)
PLUGINS_DIRECTORY: Path = PACKAGE_ROOT.parent / "plugins"

SLACK_BOT_TOKEN: str = config("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN: str = config("SLACK_APP_TOKEN")

WEBSERVER_PORT: int = config("WEBSERVER_PORT", cast=int, default=80)
WEBSERVER_HOST: str = config("WEBSERVER_HOST", default="127.0.0.1")
WEBSERVER_PATH_PREFIX: str = config("WEBSERVER_PATH_PREFIX", default="/")

MONGO_DB_HOST: str = config("MONGO_DB_HOST", default="localhost")
MONGO_DB_PORT: int = config("MONGO_DB_PORT", cast=int, default=27017)
MONGO_DB_NAME: str = config("MONGO_DB_NAME", default=PACKAGE_NAME)

MONGO_DB_URL: str = f"mongodb://{MONGO_DB_HOST}:{MONGO_DB_PORT}"