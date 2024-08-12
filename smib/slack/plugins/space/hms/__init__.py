__plugin_name__ = "Space Open/Close"
__description__ = "Space Open Close Button"
__author__ = "Sam Cork"

import re
from logging import Logger
from pprint import pformat, pprint
from urllib import request

from injectable import inject
import requests
from slack_sdk.errors import SlackApiError

from smib.common.utils import http_bolt_response
from smib.slack.custom_app import CustomApp
from slack_sdk import WebClient
from slack_sdk.web.slack_response import SlackResponse

from requests import Response

from smib.slack.db import database

from .config import HMS_CLIENT_ID, HMS_CLIENT_SECRET, HMS_BASE_URL

from .api import Hms

app: CustomApp = inject("SlackApp")


@app.event('http_get_hms')
@http_bolt_response
def get_hms_handler(say, context, ack, client, event):

    result: Response = Hms.oauth.token.POST(json={
        "grant_type": "client_credentials",
        "client_id": HMS_CLIENT_ID,
        "client_secret": HMS_CLIENT_SECRET
    })

    if not result.ok:
        return

    result_json = result.json()
    pprint(result_json)
    access_token = result_json.get("access_token", None)
    token_type = result_json.get("token_type", None)
    if None in (access_token, token_type):
        return

    result: Response = Hms.api.cc('rfid-token').POST(
        headers={
            "Content-type": "application/json",
            "Accept": "application/json",
            "Authorization": f"{token_type} {access_token}"},
        json={
            "rfidSerial": "eb362403"
        }
    )
    if not result.ok:
        return

    rfid_token_type = result.json().get("token_type", None)
    rfid_access_token = result.json().get("access_token", None)

    if None in (rfid_token_type, rfid_access_token):
        return

    result = Hms.api.users.GET(headers={
            "Content-type": "application/json",
            "Accept": "application/json",
            "Authorization": f"{rfid_token_type} {rfid_access_token}"})
    pprint(result.__dict__)
    if not result.ok:
        return

    email = result.json()['data']['email']
    result = None
    try:
        result: SlackResponse = client.users_lookupByEmail(email=email)
    except SlackApiError as e:
        print(e)

    if not result:
        return

    user_id = result.data['user']['id']
    username = result.data['user']['name']
    display_name = result.data['user']['profile']['display_name_normalized']

    return_data = {
        "id": user_id,
        "username": username,
        "display_name": display_name
    }

    pprint(return_data, sort_dicts=False)

    return return_data

