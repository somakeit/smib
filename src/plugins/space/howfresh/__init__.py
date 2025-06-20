__display_name__ = "How Fresh?"
__description__ = "How fresh is something?"

from slack_bolt.app.async_app import AsyncApp

from smib.events.interfaces.scheduled_event_interface import ScheduledEventInterface
from plugins.space.smibhid.models import SensorLog

def register(slack: AsyncApp):
    pass

async def get_latest_sensor_log_from_db() -> SensorLog:
    return await SensorLog.find_one({}, sort=[("timestamp", -1)])



