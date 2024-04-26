import json

from slack_bolt import App, CustomListenerMatcher
from injectable import inject, injectable_factory
from apscheduler.util import undefined
from apscheduler.schedulers.background import BackgroundScheduler
from slack_bolt.request import BoltRequest
import logging
from smib.common.utils import log_error

_id_func = id

logger = logging.getLogger(__name__)


@injectable_factory(BackgroundScheduler, qualifier="Scheduler", singleton=True)
def create_scheduler():
    bs = BackgroundScheduler()
    bs.start()
    logger.info("Scheduler started")
    return bs


class CustomApp(App):
    num_connections: int = 0

    def schedule(self, trigger, id, name,
                 misfire_grace_time=undefined, coalesce=undefined, max_instances=undefined,
                 next_run_time=undefined, jobstore='default', executor='default',
                 **trigger_args):
        @log_error
        def decorator_schedule(func):
            scheduler = inject(BackgroundScheduler)
            id_to_use = id

            if scheduler.get_job(id_to_use) is not None:
                id_to_use = f"{id}_{_id_func(func)}"

            event_type = f'schedule_{trigger}_{id_to_use}_{func.__name__}'

            args = None
            kwargs = {"_plugin_function": func}

            # Dispatch event in APScheduler job
            @scheduler.scheduled_job(trigger=trigger, id=id_to_use, args=args, kwargs=kwargs, name=name,
                                     misfire_grace_time=misfire_grace_time, coalesce=coalesce,
                                     max_instances=max_instances, next_run_time=next_run_time,
                                     jobstore=jobstore, executor=executor, **trigger_args)
            def dispatch_event(*args, **kwargs):
                def generate_request_body():
                    return json.dumps({
                        'type': 'event_callback',
                        'event': {
                            "type": event_type,
                        }
                    })

                self.dispatch(BoltRequest(body=generate_request_body()))  # Dispatch BoltRequest

            # The original function to be scheduled is registered as a listener to the dispatched event
            self.event(event_type)(func)

            return func

        return decorator_schedule
