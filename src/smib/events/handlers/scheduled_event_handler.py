import json

from apscheduler.job import Job
from slack_bolt import BoltResponse
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.request.async_request import AsyncBoltRequest

from smib.events import BoltEventType
from smib.events.handlers import BoltRequestMode, get_slack_signature_headers


class ScheduledEventHandler:
    def __init__(self, bolt_app: AsyncApp):
        self.bolt_app: AsyncApp = bolt_app

    async def handle(self, job: Job):
        bolt_request: AsyncBoltRequest = await to_async_bolt_request(job)
        bolt_response: BoltResponse = await self.bolt_app.async_dispatch(bolt_request)
        return bolt_response

async def to_async_bolt_request(job: Job) -> AsyncBoltRequest:
    body = {
        "type": "event_callback",
        "event": {
            "type": BoltEventType.SCHEDULED,
            "job": {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            }
        }
    }

    context: dict = {"job": job}

    json_body = json.dumps(body)
    headers = get_slack_signature_headers(json_body)

    return AsyncBoltRequest(body=json_body, mode=BoltRequestMode.SCHEDULED, context=context, headers=headers)