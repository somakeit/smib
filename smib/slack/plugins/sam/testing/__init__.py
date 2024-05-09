__author__ = "Sam Cork"

import functools

from injectable import inject
from slack_bolt import BoltRequest, BoltResponse
from threading import Thread

from smib.common.utils import http_bolt_response
from smib.slack.custom_app import CustomApp

app: CustomApp = inject("SlackApp")


def multi_run(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        comp_listeners = kwargs['request'].context.get('completed_listeners', [])
        if id(func) in comp_listeners:
            return None

        comp_listeners.append(id(func))
        returnval = func(*args, **kwargs)
        kwargs['request'].context['completed_listeners'] = comp_listeners

        return returnval

    return wrapper


@app.event("http_get_multi")
@multi_run
def multi(message, context, request: BoltRequest, ack):
    print("multi1")


@app.event("http_get_multi")
@multi_run
def multi2(message, context, request: BoltRequest, ack):
    print("multi2")

