import logging
from http import HTTPStatus
from typing import Annotated

from fastapi import Header, HTTPException

from .models import SensorLogReading, SensorLog, SensorLogRequest
from smib.events.interfaces.http_event_interface import HttpEventInterface

logger = logging.getLogger("S.M.I.B.H.I.D. - Sensor Logs")

def register(http: HttpEventInterface):

    @http.post('/smibhid/log/sensor', status_code=HTTPStatus.CREATED)
    async def log_sensor(data: SensorLogRequest, x_smibhid_hostname: Annotated[str, Header(description="Hostname of S.M.I.B.H.I.D. device")]):
        """ Logs a sensor event to the database """
        db_logs = [SensorLog.from_api(log, x_smibhid_hostname) for log in data.readings]
        logger.debug(f"Logging {len(db_logs)} sensor log(s) from {x_smibhid_hostname} to database")
        await SensorLog.insert_many(db_logs)

    @http.post('/smib/event/smibhid_sensor_log', deprecated=True)
    async def log_sensor_from_smib_event(data: SensorLogRequest, device_hostname: Annotated[str, Header(description="Hostname of S.M.I.B.H.I.D. device")]):
        """ Logs a sensor event to the database """
        db_logs = [SensorLog.from_api(log, device_hostname) for log in data.readings]
        logger.debug(f"Logging {len(db_logs)} sensor log(s) from {device_hostname} to database")
        await SensorLog.insert_many(db_logs)

    @http.get('/smibhid/log/sensor/latest')
    async def get_latest_sensor_log_from_db() -> SensorLog:
        """ Returns the latest sensor log from the database """
        latest_log = await SensorLog.find_one({}, sort=[("timestamp", -1)])

        if not latest_log:
            raise HTTPException(status_code=404, detail="No sensor logs found")
        return latest_log