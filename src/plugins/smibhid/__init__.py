__display_name__ = "S.M.I.B.H.I.D."
__description__ = "A plugin to contain SMIBHID specific interfaces"
__author__ = "sam57719"

from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, Header, HTTPException

from .models import UILog
from smib.events.interfaces.http_event_interface import HttpEventInterface


def verify_smibhid_hostname_header(x_smibhid_hostname: Annotated[str, Header(description="Hostname of S.M.I.B.H.I.D. device")]):
    """Dependency to enforce the presence of x-smibhid-hostname header"""
    return x_smibhid_hostname

def register(http: HttpEventInterface):

    http.current_router.dependencies.append(Depends(verify_smibhid_hostname_header))

    @http.post('/smibhid/log/ui', status_code=HTTPStatus.CREATED)
    async def log_ui(ui_logs: list[UILog], smibhid_hostname: Annotated[str, Header(alias="x-smibhid-hostname")]):
        await UILog.insert_many(ui_logs)
