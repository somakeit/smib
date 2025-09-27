import logging
from datetime import datetime, UTC
from http import HTTPStatus
from pprint import pformat

from slack_sdk.web.async_client import AsyncWebClient

from smib.events.interfaces.http.http_api_event_interface import ApiEventInterface
from smib.events.interfaces.scheduled_event_interface import ScheduledEventInterface
from smib.utilities import get_humanized_time, get_humanized_timedelta
from .models import SensorLogReading, SensorLog, SensorLogRequest, SensorUnit, SensorLogMonitorState
from ..common import DeviceHostnameHeader
from .config import config

logger = logging.getLogger("S.M.I.B.H.I.D. - Sensor Logs")

def _log_monitoring_settings():
    logger.info("Sensor log monitoring enabled.")
    logger.debug(f"Sensor log monitor interval: {get_humanized_timedelta(config.monitor_interval)}")
    logger.debug(f"Sensor log monitor alert threshold: {get_humanized_timedelta(config.monitor_alert_threshold)}")
    if config.monitor_alert_resend_interval is not None:
        logger.debug(f"Sensor log monitor alert resend threshold: {get_humanized_timedelta(config.monitor_alert_resend_interval)}")
    else:
        logger.debug("Sensor log monitor alert resend disabled")


async def _fetch_latest_log() -> SensorLog | None:
    latest_log = await SensorLog.get_latest_log_received()
    if not latest_log:
        logger.info("No sensor logs in DB. Skipping check.")
        return None
    logger.debug(f"Latest sensor log received {get_humanized_time(latest_log.received_timestamp)} ({latest_log.received_timestamp})")
    return latest_log


def _compute_monitor_flags(now: datetime, latest_log: SensorLog, state: SensorLogMonitorState):
    over_alert_threshold = (now - latest_log.received_timestamp) > config.monitor_alert_threshold
    over_alert_resend_threshold = (
            config.monitor_alert_resend_interval is not None
            and state.last_alert_sent is not None
            and (now - state.last_alert_sent) > config.monitor_alert_resend_interval
    )
    first_alert = over_alert_threshold and not state.alert_active
    resend_alert = over_alert_threshold and state.alert_active and over_alert_resend_threshold
    return over_alert_threshold, first_alert or resend_alert


async def _send_alert(client: AsyncWebClient, latest_log: SensorLog):
    logger.info(f"No sensor logs received within {get_humanized_timedelta(config.monitor_alert_threshold)}. Alerting.")
    await client.chat_postMessage(
        channel=config.monitor_alert_channel_id,
        text=(
            f":warning: No sensor logs received within {get_humanized_timedelta(config.monitor_alert_threshold)}. :warning:"
            f"\nLast sensor log received {get_humanized_time(latest_log.received_timestamp)} ({latest_log.received_timestamp})."
        ),
    )


async def _update_monitor_state(now: datetime, state: SensorLogMonitorState, latest_log: SensorLog, alert_active: bool, alert_sent_now: bool):
    if alert_sent_now:
        state.last_alert_sent = now
    state.alert_active = alert_active
    state.last_log_received = latest_log.received_timestamp
    state.last_check = now
    await state.save()


def setup_monitor_job(schedule: ScheduledEventInterface):
    if config.monitor_interval is None:
        logger.info("Sensor log monitoring disabled. Skipping.")
        return

    _log_monitoring_settings()

    @schedule.job("interval", seconds=config.monitor_interval.total_seconds())
    async def monitor_sensor_logs(client: AsyncWebClient):
        """ Monitors the sensor logs and alerts when none have been received within a given timeframe """
        latest_log = await _fetch_latest_log()
        if latest_log is None:
            return

        now = datetime.now(UTC)

        state: SensorLogMonitorState = await SensorLogMonitorState.find_one() or SensorLogMonitorState()
        logger.debug(f"Sensor log monitor state: {pformat(state.model_dump())}")

        over_alert_threshold, alert_now = _compute_monitor_flags(now, latest_log, state)

        if alert_now:
            await _send_alert(client, latest_log)

        await _update_monitor_state(now, state, latest_log, alert_active=over_alert_threshold, alert_sent_now=alert_now)


def setup_routes(api: ApiEventInterface):
    @api.post('/smibhid/log/sensor', status_code=HTTPStatus.CREATED)
    async def log_sensor(data: SensorLogRequest, x_smibhid_hostname: DeviceHostnameHeader):
        """ Logs a sensor event to the database """
        db_logs = [SensorLog.from_api(log, x_smibhid_hostname) for log in data.readings]
        logger.debug(f"Logging {len(db_logs)} sensor log(s) from {x_smibhid_hostname} to database")
        await SensorLog.insert_many(db_logs)
        await SensorUnit.upsert_from_api(data.units, x_smibhid_hostname)


def register(api: ApiEventInterface, schedule: ScheduledEventInterface):
    setup_routes(api)
    setup_monitor_job(schedule)