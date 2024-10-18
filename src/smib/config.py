from pathlib import Path
from decouple import config
from smib.utilities.package import get_package_root

PACKAGE_ROOT: Path = get_package_root()
PLUGINS_DIRECTORY: Path = PACKAGE_ROOT.parent / "plugins"

SLACK_BOT_TOKEN: str = config("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN: str = config("SLACK_APP_TOKEN")