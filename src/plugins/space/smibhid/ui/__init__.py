import logging
from http import HTTPStatus

from smib.events.interfaces.http.http_api_event_interface import ApiEventInterface
from .models import UILogCreate, UILog
from ..common import DeviceHostnameHeader

logger = logging.getLogger("S.M.I.B.H.I.D. - UI Logs")

def register(api: ApiEventInterface):

    @api.post('/smibhid/log/ui', status_code=HTTPStatus.CREATED)
    async def log_ui(ui_logs: list[UILogCreate], x_smibhid_hostname: DeviceHostnameHeader):
        """ Logs a UI event to the database """
        db_logs = [UILog.from_api(log, x_smibhid_hostname) for log in ui_logs]
        logger.debug(f"Logging {len(db_logs)} UI event(s) from {x_smibhid_hostname} to database")
        await UILog.insert_many(db_logs)