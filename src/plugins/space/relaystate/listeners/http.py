import logging
from datetime import timedelta
from http import HTTPStatus

from slack_bolt.app.async_app import AsyncApp

from plugins.space.smibhid.common import DeviceHostnameHeader
from smib.events.interfaces.http.http_api_event_interface import ApiEventInterface
from smib.utilities import get_humanized_timedelta
from ..common import record_relay_state_report, record_relay_state_reset
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
        logger.info(
            f"Received relay state report from {x_smibhid_hostname}: "
            f"active={relay_state_report.active}, "
            f"total_active_seconds={relay_state_report.total_active_seconds}"
        )
        outcome = await record_relay_state_report(relay_state_report, x_smibhid_hostname)

        if outcome.relay_lifetime_alert_since_reset is not None:
            message = config.relay_lifetime_alert_message_template.format(
                relay_name=config.relay_name,
                device=x_smibhid_hostname,
                duration=get_humanized_timedelta(timedelta(seconds=outcome.relay_lifetime_alert_since_reset)),
            )
            await slack.client.chat_postMessage(channel=config.relay_lifetime_alert_channel_id, text=message)

        if outcome.drift_alert is not None:
            message = (
                f":warning: Relay state total_active_seconds drift for {x_smibhid_hostname} exceeds threshold "
                f"({config.total_active_seconds_drift_warning_threshold_seconds}s): "
                f"computed_since_reset={outcome.drift_alert.since_reset}s, "
                f"reported={outcome.drift_alert.reported}s, delta={outcome.drift_alert.delta}s"
            )
            await slack.client.chat_postMessage(channel=config.drift_warning_alert_channel_id, text=message)

    @api.post("/space/relay/reset", status_code=HTTPStatus.NO_CONTENT, tags=["S.M.I.B.H.I.D."])
    async def reset_space_relay_state(
            relay_reset_report: RelayResetReport,
            x_smibhid_hostname: DeviceHostnameHeader,
    ) -> None:
        """ Record that a human reset S.M.I.B.H.I.D.'s relay on-time counter (e.g. after a filter change) """
        logger.info(
            f"Received relay reset report from {x_smibhid_hostname}: "
            f"previous_total_active_seconds={relay_reset_report.previous_total_active_seconds}"
        )
        await record_relay_state_reset(relay_reset_report, x_smibhid_hostname)
