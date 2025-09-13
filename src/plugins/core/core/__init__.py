__display_name__ = "Core"
__description__ = "Core plugin"
__author__ = "Sam Cork"

from smib.config import project
from smib.db.manager import DatabaseManager
from smib.events.interfaces.http.http_api_event_interface import ApiEventInterface

from .models import Versions, PingPong


def register(api: ApiEventInterface, database: DatabaseManager):
    @api.get("/version")
    async def get_version() -> Versions:
        return Versions(
            smib=project.version,
            mongo=await database.get_db_version()
        )

    @api.get("/ping")
    async def ping_pong() -> PingPong:
        return PingPong()

