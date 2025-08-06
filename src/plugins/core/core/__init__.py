__display_name__ = "Core"
__description__ = "Core plugin"
__author__ = "Sam Cork"

from smib.config import project
from smib.db.manager import DatabaseManager
from smib.events.interfaces.http_event_interface import HttpEventInterface
from .models import Versions, PingPong


def register(http: HttpEventInterface, database: DatabaseManager):
    @http.get("/version")
    async def get_version() -> Versions:
        return Versions(
            smib=project.version,
            mongo=await database.get_db_version()
        )

    @http.get("/ping")
    async def ping_pong() -> PingPong:
        return PingPong()

