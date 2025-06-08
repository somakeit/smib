import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import Optional

from apscheduler.job import Job
from slack_bolt.app.async_app import AsyncApp

from smib.events.interfaces.scheduled_event_interface import ScheduledEventInterface
from smib.plugins.plugin import Plugin, PythonModulePlugin
from smib.utilities.package import get_actual_module_name


class ScheduledPluginIntegration:
    def __init__(self, scheduled_event_interface: ScheduledEventInterface):
        self.scheduled_event_interface: ScheduledEventInterface = scheduled_event_interface
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    def disconnect_plugin(self, plugin: Plugin):
        self.logger.info(f"Locating and removing scheduled jobs in {plugin.unique_name} ({plugin.name})")

        module_path = Path(plugin._module.__file__)
        if module_path.name == "__init__.py":
            module_path = module_path.parent

        for job in self.scheduled_event_interface.service.scheduler.get_jobs():
            job: Job
            if hasattr(job.func, '__module__') and job.func.__module__ in sys.modules:
                job_path = sys.modules[job.func.__module__].__file__
                if Path(job_path).resolve().is_relative_to(module_path):
                    self.logger.debug(f"Removing scheduled job \"{job}\"")
                    self.scheduled_event_interface.service.scheduler.remove_job(job.id)
