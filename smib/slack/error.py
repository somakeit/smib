from slack_bolt.error import BoltUnhandledRequestError
from slack_bolt.response import BoltResponse

from http import HTTPStatus

ERRORS_TO_IGNORE = [
    BoltUnhandledRequestError
]


def handle_errors(error):
    if type(error) in ERRORS_TO_IGNORE:
        return BoltResponse(status=HTTPStatus.OK.value,
                            body=f"Ignored {error.__class__.__name__} ({error})")

    return BoltResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR.value,
                        body=f"An unhandled error occurred:\n{error.__class__.__name__} ({error})")
