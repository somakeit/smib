import logging
from http import HTTPStatus

from smib.events.interfaces.http.http_api_event_interface import ApiEventInterface
from .models import SensorLogReading, SensorLog, SensorLogRequest, SensorUnit
from ..common import DeviceHostnameHeader

logger = logging.getLogger("S.M.I.B.H.I.D. - Sensor Logs")

def register(api: ApiEventInterface):

    @api.post('/smibhid/log/sensor', status_code=HTTPStatus.CREATED)
    async def log_sensor(data: SensorLogRequest, x_smibhid_hostname: DeviceHostnameHeader):
        """ Logs a sensor event to the database """
        db_logs = [SensorLog.from_api(log, x_smibhid_hostname) for log in data.readings]
        logger.debug(f"Logging {len(db_logs)} sensor log(s) from {x_smibhid_hostname} to database")
        await SensorLog.insert_many(db_logs)

        await SensorUnit.upsert_from_api(data.units, x_smibhid_hostname)