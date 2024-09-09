import json
import pickle
from lib2to3.fixes.fix_input import context
from pprint import pprint
from sched import scheduler

from slack_bolt.async_app import AsyncApp
from slack_bolt.async_app import AsyncBoltRequest
from slack_bolt import BoltResponse
from apscheduler.job import Job
from apscheduler.schedulers.base import BaseScheduler

async def to_async_bolt_request(job: Job) -> AsyncBoltRequest:
    job_dict = {slot: getattr(job, slot, None) for slot in job.__slots__ if not slot.startswith('_')}
    body = {
        "type": "event_callback",
        "event": {
            "type": "scheduled_job",
            "job": job_dict
        }
    }

    context = {
        "job": job,
        "scheduler": job.kwargs["scheduler"]
    }

    request = AsyncBoltRequest(body=body, mode="schedule", context=context)

    return request



class AsyncSchedulerEventHandler:
    def __init__(self, app: AsyncApp):
        self.app = app

    async def handle(self, job_id: str | None = None, scheduler: BaseScheduler | None = None) -> None:
        job = scheduler.get_job(job_id)
        bolt_request = await to_async_bolt_request(job)
        await self.app.async_dispatch(bolt_request)
