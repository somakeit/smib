__display_name__ = "Relay State"
__description__ = "A plugin to keep track of relay states"
__author__ = "Sam Cork"

import logging
from http import HTTPStatus

from .common import record_relay_reset, record_relay_state_update
from .models import RelayStateUpdateRequest, RelayStateResetRequest
from smib.db.manager import DatabaseManager
from smib.events.interfaces.http.http_api_event_interface import ApiEventInterface
from ..smibhid.common import DeviceHostnameHeader

logger = logging.getLogger(__display_name__)

def register(api: ApiEventInterface, database: DatabaseManager):

    @api.post("/space/relay/state", status_code=HTTPStatus.CREATED)
    async def on_relay_state_change(
            relay_state_update: RelayStateUpdateRequest,
            x_smibhid_hostname: DeviceHostnameHeader,
    ):
        """ Handle relay state change events """
        logger.info(
            f"Received relay state update from {x_smibhid_hostname}: "
            f"active={relay_state_update.active}, "
            f"timestamp={relay_state_update.timestamp}, "
            f"total_active_seconds={relay_state_update.total_active_seconds}"
        )
        await record_relay_state_update(relay_state_update, x_smibhid_hostname)

    @api.post("/space/relay/reset", status_code=HTTPStatus.CREATED)
    async def on_relay_reset(
            relay_state_reset: RelayStateResetRequest,
            x_smibhid_hostname: DeviceHostnameHeader,
    ):
        """ Handle relay reset events """
        logger.info(
            f"Received relay reset request from {x_smibhid_hostname}: "
            f"timestamp={relay_state_reset.timestamp}, "
            f"previous_total_active_seconds={relay_state_reset.previous_total_active_seconds}"
        )
        await record_relay_reset(relay_state_reset, x_smibhid_hostname)