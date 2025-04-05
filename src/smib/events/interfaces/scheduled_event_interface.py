from functools import wraps

from apscheduler.job import Job
from apscheduler.util import undefined
from slack_bolt.app.async_app import AsyncApp

from smib.events.handlers.scheduled_event_handler import ScheduledEventHandler
from smib.events.services.scheduled_event_service import ScheduledEventService


class ScheduledEventInterface:
    def __init__(self, bolt_app: AsyncApp, handler: ScheduledEventHandler, service: ScheduledEventService):
        self.bolt_app: AsyncApp = bolt_app
        self.handler: ScheduledEventHandler = handler
        self.service: ScheduledEventService = service

    def job(
            self,
            trigger,
            id,
            name,
            misfire_grace_time=undefined,
            coalesce=undefined,
            max_instances=undefined,
            next_run_time=undefined,
            **trigger_args,
    ):
        def decorator(func: callable):
            @wraps(func)
            def wrapper():
                job: Job = self.service.scheduler.get_job(id)
                self.handler.handle(job)

            self.service.scheduler.add_job(func, trigger, id=id, name=name, misfire_grace_time=misfire_grace_time,coalesce=coalesce, max_instances=max_instances, next_run_time=next_run_time, **trigger_args)
            async def matcher(event: dict):
                return event['job']['id'] == id

            self.bolt_app.event('scheduled_job', matchers=[matcher])(func)
            return func
        return decorator




