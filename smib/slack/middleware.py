from pprint import pprint

from slack_bolt.request import BoltRequest
from slack_bolt.response import BoltResponse


def ignore_retried_events(request: BoltRequest, next: callable, event):
    pprint(request.__dict__)
    pprint(event)
    if 'x-slack-retry-num' in request.headers:
        response = BoltResponse(status=200, body="Event retried from Slack. Ignored.")
        return response
    else:
        return next()

