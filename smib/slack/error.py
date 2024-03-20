from slack_bolt.error import BoltUnhandledRequestError
from slack_bolt.response import BoltResponse
from slack_bolt.request import BoltRequest

from http import HTTPStatus
import traceback as tb
import json

ERRORS_TO_IGNORE = [
    BoltUnhandledRequestError
]


def get_http_status_json_response(http_status: HTTPStatus, error: Exception, request: BoltRequest) -> dict:
    resp = {
        "title": http_status.description,
        "status": http_status.value,
        "instance": error.__class__.__name__
    }
    headers = {"Content-Type": "application/json"}
    return {'status': http_status, 'body': json.dumps(resp), 'headers': headers}


def get_http_status_json_problem_response(http_status: HTTPStatus, error: Exception, request: BoltRequest) -> dict:
    resp = {
        "title": http_status.description,
        "status": http_status.value,
        "instance": error.__class__.__name__,
        "exception": [x.rstrip() for x in tb.format_exception_only(error)]
    }
    headers = {"Content-Type": "application/problem+json"}
    return {'status': http_status, 'body': json.dumps(resp), 'headers': headers}


def handle_errors(error, context, request):
    if type(error) in ERRORS_TO_IGNORE:
        return BoltResponse(**get_http_status_json_response(HTTPStatus.OK, error, request))

    return BoltResponse(**get_http_status_json_problem_response(HTTPStatus.IM_A_TEAPOT, error, request))
