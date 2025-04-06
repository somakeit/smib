__display_name__ = "S.M.I.B.H.I.D."
__description__ = "A plugin to contain SMIBHID specific interfaces"
__author__ = "Sam Cork"

from http import HTTPStatus
from typing import Annotated

import aiohttp
from apscheduler.job import Job
from fastapi import Header
from slack_bolt.context.ack.async_ack import AsyncAck
from slack_bolt.context.say.async_say import AsyncSay

from smib.events.interfaces.http_event_interface import HttpEventInterface
from smib.events.interfaces.scheduled_event_interface import ScheduledEventInterface
from .models import UILog, UILogCreate

def register(http: HttpEventInterface, schedule: ScheduledEventInterface):

    @http.post('/smibhid/log/ui', status_code=HTTPStatus.CREATED)
    async def log_ui(ui_logs: list[UILogCreate], x_smibhid_hostname: Annotated[str, Header(description="Hostname of S.M.I.B.H.I.D. device")]):
        db_logs = [UILog.from_api(log, x_smibhid_hostname) for log in ui_logs]
        await UILog.insert_many(db_logs)

    @http.post('/smib/event/smibhid_ui_log', deprecated=True)
    async def log_ui_from_smib_event(ui_logs: list[UILogCreate], device_hostname: Annotated[str, Header(description="Hostname of S.M.I.B.H.I.D. device")]):
        db_logs = [UILog.from_api(log, device_hostname) for log in ui_logs]
        await UILog.insert_many(db_logs)

    1/0