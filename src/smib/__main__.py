import asyncio
import logging
from asyncio import CancelledError

from slack_bolt.app.async_app import AsyncApp

from smib.config import SLACK_BOT_TOKEN
from smib.event_services import EventServiceManager
from smib.event_services.http_event_service import HttpEventService
from smib.event_services.slack_event_service import SlackEventService

async def main():
    bolt_app = AsyncApp(token=SLACK_BOT_TOKEN, raise_error_for_unhandled_request=True)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())

    event_service_manager = EventServiceManager(bolt_app)

    slack_event_service = SlackEventService(bolt_app)
    http_event_service = HttpEventService(bolt_app)

    event_service_manager.register(slack_event_service)
    event_service_manager.register(http_event_service)

    try:
        await event_service_manager.start_all()
    except (KeyboardInterrupt, CancelledError, SystemExit) as e:
        logger.info(f"Received termination: {repr(e)}")
    finally:
        await event_service_manager.stop_all()

if __name__ == '__main__':
    asyncio.run(main())