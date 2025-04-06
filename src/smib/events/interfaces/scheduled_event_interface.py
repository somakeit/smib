import logging
from asyncio import CancelledError
from functools import wraps

from apscheduler.job import Job
from apscheduler.util import undefined
from slack_bolt.app.async_app import AsyncApp

from smib.events.handlers.scheduled_event_handler import ScheduledEventHandler
from smib.events.services.scheduled_event_service import ScheduledEventService
import unicodedata


class ScheduledEventInterface:
    def __init__(self, bolt_app: AsyncApp, handler: ScheduledEventHandler, service: ScheduledEventService):
        self.bolt_app: AsyncApp = bolt_app
        self.handler: ScheduledEventHandler = handler
        self.service: ScheduledEventService = service

        self.logger = logging.getLogger(self.__class__.__name__)

    def job(
            self,
            trigger,
            id=None,
            name=None,
            misfire_grace_time=undefined,
            coalesce=undefined,
            max_instances=undefined,
            next_run_time=undefined,
            **trigger_args,
    ):
        def decorator(func: callable):
            nonlocal id, name

            id = id or func.__name__
            normalised_name = unicodedata.normalize('NFKD', func.__name__.replace('_', ' ').title()).encode('ascii', 'ignore').decode('utf-8')
            name = name or func.__doc__ or normalised_name

            @wraps(func)
            async def wrapper():
                job: Job = self.service.scheduler.get_job(id)
                try:
                    await self.handler.handle(job)
                except (KeyboardInterrupt, CancelledError, SystemExit) as e:
                    self.logger.info(f"Scheduled job \"{job}\" received termination: {repr(e)}")

            self.service.scheduler.add_job(wrapper, trigger, id=id, name=name, misfire_grace_time=misfire_grace_time,coalesce=coalesce, max_instances=max_instances, next_run_time=next_run_time, **trigger_args)
            async def matcher(event: dict):
                return event['job']['id'] == id

            self.bolt_app.event('scheduled_job', matchers=[matcher])(func)
            return func
        return decorator




