import logging

from slack_sdk.web.async_client import AsyncWebClient

from smib.events.interfaces.scheduled_event_interface import ScheduledEventInterface
from ..common import check_relay_state_for_alerts, build_relay_lifetime_alert_message, build_drift_alert_message
from ..config import config
from ..models import RelayState

logger = logging.getLogger("Space Relay State Plugin - Scheduled")


async def check_all_relay_states(client: AsyncWebClient) -> None:
    async for relay_state in RelayState.find_all():
        outcome = await check_relay_state_for_alerts(relay_state)

        if outcome.relay_lifetime_alert_since_reset is not None:
            message = build_relay_lifetime_alert_message(outcome.relay_lifetime_alert_since_reset, relay_state.device)
            await client.chat_postMessage(channel=config.relay_lifetime_alert_channel_id, text=message)

        if outcome.drift_alert is not None:
            message = build_drift_alert_message(relay_state.device, outcome.drift_alert)
            await client.chat_postMessage(channel=config.drift_warning_alert_channel_id, text=message)


def register(schedule: ScheduledEventInterface):
    if config.monitor_interval is None:
        logger.info("Relay state monitor disabled.")
        return

    logger.info(f"Relay state monitor enabled, checking every {config.monitor_interval.total_seconds()}s")

    @schedule.job("interval", seconds=config.monitor_interval.total_seconds())
    async def monitor_relay_states(client: AsyncWebClient):
        """ Periodically re-checks all known relay states for drift and relay-lifetime alerts """
        await check_all_relay_states(client)
