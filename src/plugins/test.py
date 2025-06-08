__display_name__ = "Test Plugin"
__description__ = "Test Description"

import logging

import httpx
from smib.events.interfaces.scheduled_event_interface import ScheduledEventInterface


def register(schedule: ScheduledEventInterface):
    logger = logging.getLogger(__name__)
    @schedule.job('interval', seconds=5)
    async def test_job():
        async with httpx.AsyncClient() as client:
            result = await client.get('http://localhost/space/state')
            logger.info(result.json())