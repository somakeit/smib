import logging
from http import HTTPStatus

from smib.events.interfaces.http.http_api_event_interface import ApiEventInterface
from plugins.space.smibhid.common import DeviceHostnameHeader
from ..common import record_light_state_report
from ..models import SpaceLightStateReport

logger = logging.getLogger("Space Light State Plugin - HTTP")


def register(api: ApiEventInterface):

    @api.put("/space/light/state", status_code=HTTPStatus.NO_CONTENT, tags=["S.M.I.B.H.I.D."])
    async def set_space_light_state(
            light_state_report: SpaceLightStateReport,
            x_smibhid_hostname: DeviceHostnameHeader,
    ) -> None:
        """ Report the current light-derived state of the space """
        logger.info(
            f"Received light state report from {x_smibhid_hostname}: "
            f"light_state={light_state_report.light_state}, "
            f"light_value_lux={light_state_report.light_value_lux}, "
            f"threshold_lux={light_state_report.threshold_lux}"
        )
        await record_light_state_report(light_state_report, x_smibhid_hostname)