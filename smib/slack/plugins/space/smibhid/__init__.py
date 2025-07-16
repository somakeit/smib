__plugin_name__ = "Space Open/Close"
__description__ = "Space Open Close Button"
__author__ = "Sam Cork"

from datetime import datetime
from datetime import UTC
from logging import Logger
from pprint import pformat

from pydantic import ValidationError
from injectable import inject

from smib.slack.custom_app import CustomApp
from smib.slack.db import database
from mogo.connection import Connection
from smib.common.utils import http_bolt_response
from .models.api.ui_logs import UILogs as ApiUILogs, UILog as ApiUILog
from .models.db.ui_logs import UILog as DbUILog

from .models.api.sensor_data import SensorLogs as ApiSensorLogs, SensorLog as ApiSensorLog
from .models.db.sensor_data import SensorLog as DbSensorLog

from slack_bolt.request import BoltRequest

app: CustomApp = inject("SlackApp")

def extract_device_hostname(request: BoltRequest):
    device_hostname, *_ = request.headers.get('device-hostname', [None])
    return device_hostname

@app.event("http_post_smibhid_ui_log")
@http_bolt_response
def on_smibhid_ui_log_post(event: dict, context: dict, ack: callable, request: BoltRequest):
    ack()
    logger: Logger = context.get('logger')

    device_hostname = extract_device_hostname(request)
    device_ip = event['request']['ip']

    data = event.get("data", [])
    if not data:
        logger.info("No logs received in request")
        return

    logger.debug(pformat(data))

    try:
        ui_logs = ApiUILogs(ui_logs=data)
        logger.debug(ui_logs)
    except ValidationError as e:
        logger.warning(e)
        return 400, {}

    save_api_ui_logs_to_db(ui_logs, device_ip, device_hostname)


@database()
def save_api_ui_logs_to_db(api_logs: ApiUILogs, device_ip: str, device_hostname: str | None):
    for api_log in api_logs:
        api_log: ApiUILog

        db_log = DbUILog()

        db_log.timestamp = datetime.fromtimestamp(api_log.timestamp, tz=UTC)
        db_log.type = api_log.type
        db_log.event = api_log.event.dict()

        db_log.device_hostname = device_hostname
        db_log.device_ip = device_ip

        db_log.save()

@app.event("http_post_smibhid_sensor_log")
@http_bolt_response
def on_smibhid_sensor_data_post(event: dict, context: dict, ack: callable, request: BoltRequest):
    ack()
    logger: Logger = context.get('logger')

    device_hostname = extract_device_hostname(request)
    device_ip = event['request']['ip']
    data = event.get("data", {})
    if not data:
        logger.info("No logs received in request")
        return

    logger.debug(pformat(data))

    try:
        sensor_logs = ApiSensorLogs(readings=data["readings"], units=data["units"])
        logger.debug(sensor_logs)
    except ValidationError as e:
        logger.warning(e)
        return 400, {}

    save_api_sensor_logs_to_db(sensor_logs, device_ip, device_hostname)

@database()
def save_api_sensor_logs_to_db(api_logs: ApiSensorLogs, device_ip: str, device_hostname: str | None):
    for api_log in api_logs:
        api_log: ApiSensorLog
        db_log = DbSensorLog()
        db_log.timestamp = datetime.fromtimestamp(api_log.timestamp, tz=UTC)
        db_log.data = api_log.data.model_dump()
        db_log.device_hostname = device_hostname
        db_log.device_ip = device_ip
        db_log.save()
