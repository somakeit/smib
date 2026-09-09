import logging
from http import HTTPStatus

from slack_bolt.app.async_app import AsyncApp

from plugins.space.smibhid.common import DeviceHostnameHeader, get_timestamp
from smib.events.interfaces.http.http_api_event_interface import ApiEventInterface
from smib.utilities import get_humanized_time
from ..common import record_relay_state_report, record_relay_state_reset, build_relay_lifetime_alert_message, \
    build_drift_alert_message
from ..config import config
from ..models import RelayStateReport, RelayResetReport

logger = logging.getLogger("Space Relay State Plugin - HTTP")


def register(slack: AsyncApp, api: ApiEventInterface):

    @api.post("/space/relay/state", status_code=HTTPStatus.NO_CONTENT, tags=["S.M.I.B.H.I.D."])
    async def set_space_relay_state(
            relay_state_report: RelayStateReport,
            x_smibhid_hostname: DeviceHostnameHeader,
    ) -> None:
        """ Report the current relay state of the space """
        event_timestamp = get_timestamp(relay_state_report.timestamp)
        logger.info(
            f"Received relay state report from {x_smibhid_hostname}: "
            f"active={relay_state_report.active}, "
            f"total_active_seconds={relay_state_report.total_active_seconds}, "
            f"timestamp={get_humanized_time(event_timestamp)} ({event_timestamp})"
        )
        outcome = await record_relay_state_report(relay_state_report, x_smibhid_hostname)

        if outcome.relay_lifetime_alert_since_reset is not None:
            message = build_relay_lifetime_alert_message(outcome.relay_lifetime_alert_since_reset, x_smibhid_hostname)
            await slack.client.chat_postMessage(channel=config.relay_lifetime_alert_channel_id, text=message)

        if outcome.drift_alert is not None:
            message = build_drift_alert_message(x_smibhid_hostname, outcome.drift_alert)
            await slack.client.chat_postMessage(channel=config.drift_warning_alert_channel_id, text=message)

    @api.post("/space/relay/reset", status_code=HTTPStatus.NO_CONTENT, tags=["S.M.I.B.H.I.D."])
    async def reset_space_relay_state(
            relay_reset_report: RelayResetReport,
            x_smibhid_hostname: DeviceHostnameHeader,
    ) -> None:
        """ Record that a human reset S.M.I.B.H.I.D.'s relay on-time counter (e.g. after a filter change) """
        event_timestamp = get_timestamp(relay_reset_report.timestamp)
        logger.info(
            f"Received relay reset report from {x_smibhid_hostname}: "
            f"previous_total_active_seconds={relay_reset_report.previous_total_active_seconds}, "
            f"timestamp={get_humanized_time(event_timestamp)} ({event_timestamp})"
        )
        await record_relay_state_reset(relay_reset_report, x_smibhid_hostname)
