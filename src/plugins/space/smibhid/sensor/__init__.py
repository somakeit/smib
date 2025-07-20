import logging
from http import HTTPStatus
from typing import Annotated

from fastapi import Header, HTTPException

from .models import SensorLogReading, SensorLog, SensorLogRequest, SensorUnits
from smib.events.interfaces.http_event_interface import HttpEventInterface
from ..common import DeviceHostnameHeader

logger = logging.getLogger("S.M.I.B.H.I.D. - Sensor Logs")

def register(http: HttpEventInterface):

    @http.post('/smibhid/log/sensor', status_code=HTTPStatus.CREATED)
    async def log_sensor(data: SensorLogRequest, x_smibhid_hostname: DeviceHostnameHeader):
        """ Logs a sensor event to the database """
        db_logs = [SensorLog.from_api(log, x_smibhid_hostname) for log in data.readings]
        logger.debug(f"Logging {len(db_logs)} sensor log(s) from {x_smibhid_hostname} to database")
        await SensorLog.insert_many(db_logs)

        await SensorUnits.upsert_from_api(data.units, x_smibhid_hostname)

    @http.post('/smib/event/smibhid_sensor_log', deprecated=True)
    async def log_sensor_from_smib_event(data: SensorLogRequest, device_hostname: DeviceHostnameHeader):
        """ Logs a sensor event to the database """
        db_logs = [SensorLog.from_api(log, device_hostname) for log in data.readings]
        logger.debug(f"Logging {len(db_logs)} sensor log(s) from {device_hostname} to database")
        await SensorLog.insert_many(db_logs)

        await SensorUnits.upsert_from_api(data.units, device_hostname)

