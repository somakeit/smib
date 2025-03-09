__display_name__ = "S.M.I.B.H.I.D."
__description__ = "A plugin to contain SMIBHID specific interfaces"
__author__ = "sam57719"

from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, Header, HTTPException

from .models import UILog, UILogCreate
from smib.events.interfaces.http_event_interface import HttpEventInterface


def ensure_smibhid_hostname_header(
        x_smibhid_hostname: Annotated[str, Header(description="Hostname of S.M.I.B.H.I.D. device")] = None,
        device_hostname: Annotated[str, Header(description="Hostname of S.M.I.B.H.I.D. device", deprecated=True)] = None,
):
    """Dependency to enforce the presence of x-smibhid-hostname header"""
    if not x_smibhid_hostname and not device_hostname:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Missing x-smibhid-hostname header")
    return x_smibhid_hostname or device_hostname

def register(http: HttpEventInterface):

    http.current_router.dependencies.append(Depends(ensure_smibhid_hostname_header))

    @http.post('/smibhid/log/ui', status_code=HTTPStatus.CREATED)
    async def log_ui(ui_logs: list[UILogCreate], smibhid_hostname: Annotated[str, Depends(ensure_smibhid_hostname_header)]):
        db_logs = [UILog.from_api(log, smibhid_hostname) for log in ui_logs]
        print(ui_logs)
        print(db_logs)
        await UILog.insert_many(db_logs)

    @http.post('/smib/event/smibhid_ui_log', deprecated=True)
    async def log_ui_from_smib_event(ui_logs: list[UILogCreate], smibhid_hostname: Annotated[str, Depends(ensure_smibhid_hostname_header)]):
        db_logs = [UILog.from_api(log, smibhid_hostname) for log in ui_logs]
        print(ui_logs)
        print(db_logs)
        await UILog.insert_many(db_logs)