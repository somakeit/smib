__display_name__ = "Space State Metrics"
__description__ = "A plugin to push space state metrics (heatmap) to InfluxDB."
__author__ = "Sam Cork"

import logging
from typing import TYPE_CHECKING

from plugins.metrics.common import config as metrics_config
from smib.db.manager import DatabaseManager
from smib.events.interfaces.scheduled_event_interface import ScheduledEventInterface
from .config import config

if TYPE_CHECKING:
    from plugins.space.spacestate.models import SpaceStateEventHistory

logger = logging.getLogger(__display_name__)

def register(schedule: ScheduledEventInterface, database: DatabaseManager):
    if not metrics_config.enabled:
        logger.info("Metrics are disabled. Skipping.")
        return

    _SpaceStateEventHistory: type[SpaceStateEventHistory] | None = None

    @schedule.job("interval", seconds=config.monitor_interval.total_seconds())
    async def monitor_spacestate_event_history_for_new_metrics():
        """ Monitors the space state event history for new open periods and pushes them to InfluxDB """
        nonlocal _SpaceStateEventHistory
        if _SpaceStateEventHistory is None:
            _SpaceStateEventHistory = database.find_model_by_name("SpaceStateEventHistory")

        # Create an async generator for the unsynced events
        # noinspection PyComparisonWithNone
        unsynced_iterator = _SpaceStateEventHistory.find(
            _SpaceStateEventHistory.metrics_exported_at == None
        ).sort(+_SpaceStateEventHistory.timestamp)

        # Check if we have anything to process
        if await unsynced_iterator.count() == 0:
            logger.debug("No unsynced events found. Skipping metrics export.")
            return

        async for event in unsynced_iterator:
            # Process each event one by one
            logger.debug(f"Processing event: {event.timestamp} - {event.new_state}")
            # ... explosion logic ...




