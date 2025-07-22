from smib.config.general import GeneralSettings
from smib.config.project import ProjectSettings
from smib.config.slack import SlackSettings
from smib.config.database import DatabaseSettings
from smib.config.webserver import WebserverSettings
from smib.config._env_base_settings import EnvBaseSettings

__all__ = ["project", "general", "slack", "database", "webserver", "EnvBaseSettings"]

project = ProjectSettings()
general = GeneralSettings()
slack = SlackSettings()
database = DatabaseSettings()
webserver = WebserverSettings()