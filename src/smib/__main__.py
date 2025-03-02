import asyncio
import inspect
import logging
import sys
from asyncio import CancelledError
from pathlib import Path
from types import ModuleType

from fastapi.routing import APIRoute
from slack_bolt.app.async_app import AsyncApp
from starlette.routing import BaseRoute

from smib.config import SLACK_BOT_TOKEN
from smib.error_handler import error_handler
from smib.events.handlers.http_event_handler import HttpEventHandler
from smib.events.interfaces.http_event_interface import HttpEventInterface
from smib.events.services import EventServiceManager
from smib.events.services.http_event_service import HttpEventService
from smib.events.services.slack_event_service import SlackEventService
from smib.plugins.lifecycle_manager import PluginLifecycleManager

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] [%(asctime)s] %(name)s: %(message)s',
    force=True
)

async def main():
    bolt_app = AsyncApp(
        token=SLACK_BOT_TOKEN,
        raise_error_for_unhandled_request=True,
        request_verification_enabled=False, #TODO Add proper slack request signature
        process_before_response=True
    )
    bolt_app.error(error_handler)

    logger = logging.getLogger(__name__)

    # Most of the slack stuff is handled by the SlackBolt Framework
    slack_event_service = SlackEventService(bolt_app)

    http_event_service = HttpEventService(bolt_app)
    http_event_handler = HttpEventHandler(bolt_app)
    http_event_interface = HttpEventInterface(bolt_app, http_event_handler, http_event_service)

    event_service_manager = EventServiceManager()
    event_service_manager.register(slack_event_service)
    event_service_manager.register(http_event_service)

    plugin_lifecycle_manager = PluginLifecycleManager(bolt_app)
    plugin_lifecycle_manager.register_parameter('slack', bolt_app)
    plugin_lifecycle_manager.register_parameter('http', http_event_interface)
    plugin_lifecycle_manager.register_parameter('_socket_mode_handler', slack_event_service.service)

    plugin_lifecycle_manager.register_plugin_unregister_callback(slack_event_service.disconnect_module)
    plugin_lifecycle_manager.register_plugin_unregister_callback(http_event_service.disconnect_module)
    plugin_lifecycle_manager.load_plugins()

    try:
        await event_service_manager.start_all()
    except (KeyboardInterrupt, CancelledError, SystemExit) as e:
        logger.info(f"Received termination: {repr(e)}")
    except Exception as e:
        logger.exception(f"Unexpected exception: {repr(e)}", exc_info=True)
    finally:
        await event_service_manager.stop_all()

if __name__ == '__main__':
    asyncio.run(main())