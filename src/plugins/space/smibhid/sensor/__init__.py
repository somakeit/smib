import logging
from datetime import datetime, UTC
from http import HTTPStatus
from pprint import pformat

from apscheduler.job import Job
from slack_sdk.web.async_client import AsyncWebClient

from smib.events.interfaces.http.http_api_event_interface import ApiEventInterface
from smib.events.interfaces.scheduled_event_interface import ScheduledEventInterface
from smib.utilities import get_humanized_time, get_humanized_timedelta
from .models import SensorLogReading, SensorLog, SensorLogRequest, SensorUnit, SensorLogMonitorState
from ..common import DeviceHostnameHeader
from .config import config

logger = logging.getLogger("S.M.I.B.H.I.D. - Sensor Logs")

def register(api: ApiEventInterface, schedule: ScheduledEventInterface):

    @api.post('/smibhid/log/sensor', status_code=HTTPStatus.CREATED)
    async def log_sensor(data: SensorLogRequest, x_smibhid_hostname: DeviceHostnameHeader):
        """ Logs a sensor event to the database """
        db_logs = [SensorLog.from_api(log, x_smibhid_hostname) for log in data.readings]
        logger.debug(f"Logging {len(db_logs)} sensor log(s) from {x_smibhid_hostname} to database")
        await SensorLog.insert_many(db_logs)

        await SensorUnit.upsert_from_api(data.units, x_smibhid_hostname)

    # Setup sensor log monitoring job if enabled
    if config.monitor_interval is not None:
        logger.info("Sensor log monitoring enabled.")

        logger.debug(f"Sensor log monitor interval: {get_humanized_timedelta(config.monitor_interval)}")
        logger.debug(f"Sensor log monitor alert threshold: {get_humanized_timedelta(config.monitor_alert_threshold)}")
        if config.monitor_alert_resend_interval is not None:
            logger.debug(f"Sensor log monitor alert resend threshold: {get_humanized_timedelta(config.monitor_alert_resend_interval)}")
        else:
            logger.debug("Sensor log monitor alert resend disabled")

        @schedule.job("interval", seconds=config.monitor_interval.total_seconds())
        async def monitor_sensor_logs(client: AsyncWebClient):
            """ Monitors the sensor logs and alerts when none have been received within a given timeframe """
            latest_log: SensorLog | None = await SensorLog.get_latest_log_received()
            if not latest_log:
                logger.info("No sensor logs in DB. Skipping check.")
                return

            logger.debug(f"Latest sensor log received {get_humanized_time(latest_log.received_timestamp)} ({latest_log.received_timestamp})")

            sensor_monitor_state: SensorLogMonitorState = await SensorLogMonitorState.find_one() or SensorLogMonitorState()
            over_alert_threshold: bool = (datetime.now(UTC) - latest_log.received_timestamp) > config.monitor_alert_threshold
            over_alert_resend_threshold: bool = (
                config.monitor_alert_resend_interval is not None
                and sensor_monitor_state.last_alert_sent is not None
                and (datetime.now(UTC) - sensor_monitor_state.last_alert_sent) > config.monitor_alert_resend_interval
            )

            logger.debug(f"Sensor log monitor state: {pformat(sensor_monitor_state.model_dump())}")

            alert_now = over_alert_threshold and not sensor_monitor_state.alert_active or over_alert_threshold and sensor_monitor_state.alert_active and over_alert_resend_threshold
            if alert_now:
                logger.info(f"No sensor logs received within {get_humanized_timedelta(config.monitor_alert_threshold)}. Alerting.")
                await client.chat_postMessage(
                    channel=config.monitor_alert_channel_id,
                    text=f":warning: No sensor logs received within {get_humanized_timedelta(config.monitor_alert_threshold)}. :warning:"
                         f"\nLast sensor log received {get_humanized_time(latest_log.received_timestamp)} ({latest_log.received_timestamp})."
                )
                sensor_monitor_state.last_alert_sent = datetime.now(UTC)

            # Update before exiting
            sensor_monitor_state.alert_active = over_alert_threshold
            sensor_monitor_state.last_log_received = latest_log.received_timestamp
            sensor_monitor_state.last_check = datetime.now(UTC)
            await sensor_monitor_state.save()
    else:
        logger.info("Sensor log monitoring disabled. Skipping.")





