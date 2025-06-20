__display_name__ = "Core"
__description__ = "Core plugin"
__author__ = "Sam Cork"

from smib.config import PACKAGE_VERSION
from smib.db.manager import DatabaseManager
from smib.events.interfaces.http_event_interface import HttpEventInterface
from .models import Versions


def register(http: HttpEventInterface, database: DatabaseManager):
    @http.get("/version")
    async def get_version() -> Versions:
        return Versions(
            smib=PACKAGE_VERSION,
            mongo=await database.get_db_version()
        )
