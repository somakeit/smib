__display_name__ = "S.M.I.B.H.I.D."
__description__ = "A plugin to contain SMIBHID specific interfaces"
__author__ = "Sam Cork"

import logging
from http import HTTPStatus
from typing import Annotated

from fastapi import Header, HTTPException
from slack_bolt.app.async_app import AsyncApp

from smib.events.interfaces.http_event_interface import HttpEventInterface
from smib.events.interfaces.scheduled_event_interface import ScheduledEventInterface
from .models import UILog, UILogCreate, SensorLog, SensorLogCreate

logger = logging.getLogger(__display_name__)

def register(http: HttpEventInterface, schedule: ScheduledEventInterface, slack: AsyncApp):

    @http.post('/smibhid/log/ui', status_code=HTTPStatus.CREATED)
    async def log_ui(ui_logs: list[UILogCreate], x_smibhid_hostname: Annotated[str, Header(description="Hostname of S.M.I.B.H.I.D. device")]):
        """ Logs a UI event to the database """
        db_logs = [UILog.from_api(log, x_smibhid_hostname) for log in ui_logs]
        logger.debug(f"Logging {len(db_logs)} UI event(s) from {x_smibhid_hostname} to database")
        await UILog.insert_many(db_logs)

    @http.post('/smibhid/log/sensor', status_code=HTTPStatus.CREATED)
    async def log_sensor(sensor_logs: list[SensorLogCreate], x_smibhid_hostname: Annotated[str, Header(description="Hostname of S.M.I.B.H.I.D. device")]):
        """ Logs a sensor event to the database """
        db_logs = [SensorLog.from_api(log, x_smibhid_hostname) for log in sensor_logs]
        logger.debug(f"Logging {len(db_logs)} sensor log(s) from {x_smibhid_hostname} to database")
        await SensorLog.insert_many(db_logs)

    @http.post('/smib/event/smibhid_ui_log', deprecated=True)
    async def log_ui_from_smib_event(ui_logs: list[UILogCreate], device_hostname: Annotated[str, Header(description="Hostname of S.M.I.B.H.I.D. device")]):
        """ Logs a UI event to the database """
        db_logs = [UILog.from_api(log, device_hostname) for log in ui_logs]
        logger.debug(f"Logging {len(db_logs)} UI event(s) from {device_hostname} to database")
        await UILog.insert_many(db_logs)

    @http.post('/smib/event/smibhid_sensor_log', deprecated=True)
    async def log_sensor_from_smib_event(sensor_logs: list[SensorLogCreate], device_hostname: Annotated[str, Header(description="Hostname of S.M.I.B.H.I.D. device")]):
        """ Logs a sensor event to the database """
        db_logs = [SensorLog.from_api(log, device_hostname) for log in sensor_logs]
        logger.debug(f"Logging {len(db_logs)} sensor log(s) from {device_hostname} to database")   
        await SensorLog.insert_many(db_logs)

    @http.get('/smibhid/log/sensor/latest')
    async def get_latest_sensor_log_from_db() -> SensorLog:
        """ Returns the latest sensor log from the database """
        latest_log = await SensorLog.find_one({}, sort=[("timestamp", -1)])
        
        if not latest_log:
            raise HTTPException(status_code=404, detail="No sensor logs found")
        return latest_log