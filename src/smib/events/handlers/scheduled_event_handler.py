from apscheduler.job import Job
from fastapi.encoders import jsonable_encoder
from slack_bolt import BoltResponse
from slack_bolt.adapter.starlette.async_handler import to_starlette_response
from slack_bolt.app.async_app import AsyncApp
from fastapi import Request, Response
from slack_bolt.request.async_request import AsyncBoltRequest

from smib.events.handlers import BoltRequestMode
from smib.events.responses.http_bolt_response import HttpBoltResponse


class ScheduledEventHandler:
    def __init__(self, bolt_app: AsyncApp):
        self.bolt_app: AsyncApp = bolt_app

    async def handle(self, job: Job):
        bolt_request: AsyncBoltRequest = await to_async_bolt_request(job)
        bolt_response: BoltResponse = await self.bolt_app.async_dispatch(bolt_request)
        return bolt_response

async def to_async_bolt_request(job: Job) -> AsyncBoltRequest:
    job_dict = {slot: getattr(job, slot, None) for slot in job.__slots__ if not slot.startswith('_')}
    body = {
        "type": "event_callback",
        "event": {
            "type": "scheduled_job",
            "job": job_dict
        }
    }
    context: dict = {"job": job}
    return AsyncBoltRequest(body=body, mode=BoltRequestMode.SCHEDULED, context=context)