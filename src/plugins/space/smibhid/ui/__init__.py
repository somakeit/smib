import logging
from http import HTTPStatus
from typing import Annotated

from fastapi import Header

from .models import UILogCreate, UILog
from smib.events.interfaces.http_event_interface import HttpEventInterface

logger = logging.getLogger("S.M.I.B.H.I.D. - UI Logs")

def register(http: HttpEventInterface):

    @http.post('/smibhid/log/ui', status_code=HTTPStatus.CREATED)
    async def log_ui(ui_logs: list[UILogCreate], x_smibhid_hostname: Annotated[str, Header(description="Hostname of S.M.I.B.H.I.D. device")]):
        """ Logs a UI event to the database """
        db_logs = [UILog.from_api(log, x_smibhid_hostname) for log in ui_logs]
        logger.debug(f"Logging {len(db_logs)} UI event(s) from {x_smibhid_hostname} to database")
        await UILog.insert_many(db_logs)

    @http.post('/smib/event/smibhid_ui_log', deprecated=True)
    async def log_ui_from_smib_event(ui_logs: list[UILogCreate], device_hostname: Annotated[str, Header(description="Hostname of S.M.I.B.H.I.D. device")]):
        """ Logs a UI event to the database """
        db_logs = [UILog.from_api(log, device_hostname) for log in ui_logs]
        logger.debug(f"Logging {len(db_logs)} UI event(s) from {device_hostname} to database")
        await UILog.insert_many(db_logs)