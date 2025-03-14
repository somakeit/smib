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
        smib_version = PACKAGE_VERSION
        python_version = ".".join(map(str, sys.version_info[:3]))
        return Version(smib=smib_version, python=python_version)
