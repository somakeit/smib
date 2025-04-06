import logging
import sys
from pathlib import Path
from types import ModuleType

from apscheduler.job import Job
from slack_bolt.app.async_app import AsyncApp

from smib.events.interfaces.scheduled_event_interface import ScheduledEventInterface
from smib.utilities.package import get_actual_module_name


class ScheduledPluginIntegration:
    def __init__(self, scheduled_event_interface: ScheduledEventInterface):
        self.scheduled_event_interface: ScheduledEventInterface = scheduled_event_interface
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    def disconnect_plugin(self, plugin: ModuleType):
        self.logger.info(f"Locating scheduled jobs in {plugin.__name__} ({get_actual_module_name(plugin)})")
        module_path = Path(plugin.__file__)
        if module_path.name == "__init__.py":
            module_path = module_path.parent

        for job in self.scheduled_event_interface.service.scheduler.get_jobs():
            job: Job
            job_path = sys.modules[job.func.__module__].__file__
            if Path(job_path).resolve().is_relative_to(module_path):
                self.logger.info(f"Removing scheduled job \"{job}\"")
                self.scheduled_event_interface.service.scheduler.remove_job(job.id)
