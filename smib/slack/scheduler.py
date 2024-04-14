from functools import wraps
from pprint import pprint

from injectable import inject, injectable_factory, autowired, Autowired, injectable
from slack_bolt import App
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.util import undefined

from slack_bolt.request import BoltRequest


@injectable_factory(BackgroundScheduler, singleton=True, qualifier="Scheduler")
def create_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.start()
    return scheduler


def generate_request_body(job_id):
    event_type = f"schedule_{job_id}"
    return {
        'type': 'event_callback',
        'event': {
            "type": event_type,
        }
    }


# def schedule(trigger, id, args=None, kwargs=None, name=None,
#              misfire_grace_time=undefined, coalesce=undefined, max_instances=undefined,
#              next_run_time=undefined, jobstore='default', executor='default',
#              **trigger_args):
#     app = inject(App)
#     scheduler = inject(BackgroundScheduler)
#     print(scheduler)
#     # # Get the job specific decorator from apscheduler.scheduled_job
#     # job_decorator = scheduler.scheduled_job(trigger, args=args, kwargs=kwargs, id=id, name=name,
#     #                                         misfire_grace_time=misfire_grace_time,
#     #                                         coalesce=coalesce, max_instances=max_instances,
#     #                                         next_run_time=next_run_time, jobstore=jobstore,
#     #                                         executor=executor, **trigger_args)
#
#     def decorator_schedule_and_dispatch(func):
#         event_type = f'schedule_{id}'
#         print(event_type)
#
#         app.event(event_type)(func)
#
#         @scheduler.scheduled_job(trigger, args=args, kwargs=kwargs, id=id, name=name,
#                                  misfire_grace_time=misfire_grace_time,
#                                  coalesce=coalesce, max_instances=max_instances,
#                                  next_run_time=next_run_time, jobstore=jobstore,
#                                  executor=executor, **trigger_args)
#         def wrapper():
#             bolt_request: BoltRequest = BoltRequest(body=generate_request_body(id))
#             pprint(bolt_request)
#             app.dispatch(bolt_request)
#
#         return wrapper
#
#     return decorator_schedule_and_dispatch

def schedule(func):
    print('registered' + func.__name__)
    def wrapper():
        print("Something is happening before the function is called.")
        func()
        print("Something is happening after the function is called.")
    return wrapper

@autowired
def attach_scheduler(app: Autowired(App)):
    app.schedule = schedule
    print(app.schedule)
