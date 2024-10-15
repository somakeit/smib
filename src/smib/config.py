from pathlib import Path
from decouple import config

SLACK_BOT_TOKEN: str = config("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN: str = config("SLACK_APP_TOKEN")

PLUGINS_DIRECTORY: Path = config("PLUGINS_DIRECTORY", cast=Path, default=Path('../plugins'))