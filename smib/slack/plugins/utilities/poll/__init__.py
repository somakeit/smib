__plugin_name__ = "SMIB Poll"
__description__ = "Create and track polls"
__author__ = "Sam Cork"

from datetime import timedelta
from logging import Logger
from pprint import pformat

from apscheduler.triggers.cron import CronTrigger
from injectable import inject
from slack_sdk.web import SlackResponse

from smib.slack.db import database
from .views import CreatePollModal
from smib.slack.custom_app import CustomApp
from slack_sdk.web.client import WebClient

from .models import View as DBView

from smib.common.utils import get_utc_datetime

app: CustomApp = inject("SlackApp")


@app.global_shortcut('smib-poll')
@database()
def smib_poll_shortcut(body, payload, ack, client: WebClient, context: dict):
    ack()
    logger: Logger = context.get("logger")

    poll_modal = CreatePollModal()

    resp: SlackResponse | None
    try:
        resp: SlackResponse = client.views_open(
            trigger_id=payload["trigger_id"],
            view=poll_modal
        )

        view = resp.data.get('view', {})
        view_id = view.get('id')
        external_id = view.get('external_id')

        DBView.store(external_id=external_id, view_id=view_id, view_json=poll_modal.to_dict())
    except Exception as e:
        logger.exception(e)


@app.block_action("add_option")
@database()
def add_option(ack, payload: dict, body, request, context: dict, client: WebClient):
    ack()

    logger: Logger = context.get("logger")

    view = body.get('view', {})
    view_id = view.get('id')
    external_id = view.get('external_id')

    view = DBView.retrieve(view_id=view_id)
    logger.debug(view)

    new_view = CreatePollModal.from_dict(view.view_json)
    new_view.add_option()

    try:
        resp = client.views_update(view=new_view, view_id=view_id)
        DBView.store(external_id=external_id, view_id=view_id, view_json=new_view.to_dict())
        logger.debug(resp.data)
    except Exception as e:
        logger.exception(e)


@app.block_action("remove_option")
@database()
def remove_option(ack, payload: dict, body, request, context: dict, client: WebClient):
    ack()

    logger: Logger = context.get("logger")

    view = body.get('view', {})
    view_id = view.get('id')
    external_id = view.get('external_id')

    view = DBView.retrieve(view_id=view_id)
    logger.debug(view)

    new_view = CreatePollModal.from_dict(view.view_json)
    new_view.remove_option()

    try:
        resp = client.views_update(view=new_view, view_id=view_id)
        DBView.store(external_id=external_id, view_id=view_id, view_json=new_view.to_dict())
        logger.debug(resp.data)
    except Exception as e:
        logger.exception(e)


@app.schedule(CronTrigger.from_crontab('*/10 * * * *'), id='poll_housekeeping', name='Poll Housekeeping')
@database()
def housekeeping(context, event):
    """
    Housekeeping task that clears up any old cached views in the DB that are more than an hour old.
    Runs every 10 minutes
    """
    logger: Logger = context.get("logger")
    logger.debug(pformat(event))

    logger.debug('Looking for expired views in the DB')

    one_hour_ago = get_utc_datetime() - timedelta(hours=1)
    docs_to_delete = DBView.find({
        '$or': [
            {'last_modified': {'$lt': one_hour_ago}},
            {'last_modified': None}
        ]
    })

    if docs_to_delete:
        logger.debug(f'Deleting {len(docs_to_delete)} view(s) from the DB')

    for doc in docs_to_delete:
        doc.delete()


