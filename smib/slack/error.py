from injectable import inject
from slack_bolt.error import BoltUnhandledRequestError
from slack_bolt.response import BoltResponse
from slack_bolt.request import BoltRequest

from http import HTTPStatus
import traceback as tb
import json
from smib.common.config import ROOT_DIRECTORY
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

ERRORS_TO_IGNORE = [
    BoltUnhandledRequestError
]


def get_http_status_json_response(http_status: HTTPStatus, error: Exception, request: BoltRequest) -> dict:
    resp = {
        "title": http_status.description,
        "status": http_status.value,
        "instance": error.__class__.__name__
    }
    headers = {"Content-Type": "application/json", 'x-slack-no-retry': 1}
    return {'status': http_status, 'body': json.dumps(resp), 'headers': headers}


def get_http_status_json_problem_response(http_status: HTTPStatus, error: Exception, request: BoltRequest) -> dict:
    error_frames = tb.extract_tb(error.__traceback__)
    last_frame = error_frames[-1]

    try:
        file = Path(last_frame.filename).relative_to(ROOT_DIRECTORY).as_posix()
    except Exception as e:
        file = None

    resp = {
        "title": http_status.description,
        "status": http_status.value,
        "instance": error.__class__.__name__,
        "exception": [x.rstrip() for x in tb.format_exception_only(error)],
        "file": file,
        "function": last_frame.name,
        "traceback": [x for t in tb.format_exception(error) for x in t.split('\n') if len(x) > 0]
    }
    headers = {"Content-Type": "application/problem+json", 'x-slack-no-retry': 1}
    return {'status': http_status, 'body': json.dumps(resp), 'headers': headers}


def handle_errors(error, context, request, body):
    print(context)
    if type(error) in ERRORS_TO_IGNORE:
        resp = BoltResponse(**get_http_status_json_response(HTTPStatus.OK, error, request))
        context.ack()
        return resp

    resp = BoltResponse(**get_http_status_json_problem_response(HTTPStatus.IM_A_TEAPOT, error, request))
    context.ack()
    return resp

