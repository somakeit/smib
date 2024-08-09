__plugin_name__ = "Space Open/Close"
__description__ = "Space Open Close Button"
__author__ = "Sam Cork"

from datetime import datetime
from logging import Logger
from pprint import pformat

from pydantic import ValidationError
from injectable import inject

from smib.slack.custom_app import CustomApp
from smib.slack.db import database
from mogo.connection import Connection
from smib.common.utils import http_bolt_response
from .models.api import UILogs as ApiUILogs, UILog as ApiUILog
from .models.db import UILog as DbUILog

from slack_bolt.request import BoltRequest

app: CustomApp = inject("SlackApp")


@app.event("http_post_smibhid_ui_log")
@http_bolt_response
def on_smibhid_ui_log_post(event: dict, context: dict, ack: callable, request: BoltRequest):
    ack()
    logger: Logger = context.get('logger')

    device_hostname, *_ = request.headers.get('device-hostname', None)
    device_ip = event['request']['ip']

    logger.debug(pformat(event))

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

    save_api_logs_to_db(ui_logs, device_ip, device_hostname)


@database()
def save_api_logs_to_db(api_logs: ApiUILogs, device_ip: str, device_hostname: str | None):
    for api_log in api_logs:
        api_log: ApiUILog

        db_log = DbUILog()

        db_log.timestamp = datetime.utcfromtimestamp(api_log.timestamp)
        db_log.type = api_log.type
        db_log.event = api_log.event.dict()

        db_log.device_hostname = device_hostname
        db_log.device_ip = device_ip

        db_log.save()
