__display_name__ = "Core"
__description__ = ""
__author__ = "Sam Cork"

from smib.config import PACKAGE_VERSION
from smib.events.interfaces.http_event_interface import HttpEventInterface
import sys
from .models import Version


def register(http: HttpEventInterface):
    @http.get("/version")
    async def get_version() -> Version:
        return Version(
            smib=PACKAGE_VERSION,
            python=".".join(map(str, sys.version_info[:3]))
        )
