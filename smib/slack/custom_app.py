import json

from slack_bolt import App
from injectable import inject, injectable
from apscheduler.util import undefined
from apscheduler.schedulers.background import BackgroundScheduler
from slack_bolt.request import BoltRequest

_id_func = id

class CustomApp(App):
    def schedule(self, trigger, id, args=None, kwargs=None, name=None,
                 misfire_grace_time=undefined, coalesce=undefined, max_instances=undefined,
                 next_run_time=undefined, jobstore='default', executor='default',
                 **trigger_args):
        def decorator_schedule(func):
            event_type = f'schedule_{trigger}_{id}_{func.__name__}_{_id_func(func)}'
            print(event_type)
            scheduler = inject(BackgroundScheduler)

            # Dispatch event in APScheduler job
            @scheduler.scheduled_job(trigger=trigger, id=id, args=args, kwargs=kwargs, name=name,
                                     misfire_grace_time=misfire_grace_time, coalesce=coalesce,
                                     max_instances=max_instances, next_run_time=next_run_time,
                                     jobstore=jobstore, executor=executor, **trigger_args)
            def dispatch_event():
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

