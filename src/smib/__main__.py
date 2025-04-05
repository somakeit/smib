import asyncio
import logging
from asyncio import CancelledError

from slack_bolt.app.async_app import AsyncApp

from smib.config import SLACK_BOT_TOKEN, PACKAGE_DISPLAY_NAME
from smib.db.manager import DatabaseManager
from smib.error_handler import error_handler
from smib.events.handlers.http_event_handler import HttpEventHandler
from smib.events.interfaces.http_event_interface import HttpEventInterface
from smib.events.services import EventServiceManager
from smib.events.services.http_event_service import HttpEventService
from smib.events.services.scheduled_event_service import ScheduledEventService
from smib.events.services.slack_event_service import SlackEventService
from smib.plugins.integrations.http_plugin_integration import HttpPluginIntegration
from smib.plugins.integrations.slack_plugin_integration import SlackPluginIntegration
from smib.plugins.lifecycle_manager import PluginLifecycleManager
from smib.plugins.locator import PluginLocator

from smib.logging_ import initialise_logging


async def main():
    initialise_logging()

    bolt_app = AsyncApp(
        name=PACKAGE_DISPLAY_NAME,
        token=SLACK_BOT_TOKEN,
        raise_error_for_unhandled_request=True,
        request_verification_enabled=False, #TODO Add proper slack request signature
        process_before_response=True
    )
    bolt_app.error(error_handler)

    logger = logging.getLogger(__name__)

    # Most of the slack stuff is handled by the SlackBolt Framework
    slack_event_service = SlackEventService(bolt_app)

    http_event_service = HttpEventService()
    http_event_handler = HttpEventHandler(bolt_app)
    http_event_interface = HttpEventInterface(bolt_app, http_event_handler, http_event_service)

    scheduled_event_service = ScheduledEventService()

    event_service_manager = EventServiceManager()
    event_service_manager.register(slack_event_service)
    event_service_manager.register(http_event_service)
    event_service_manager.register(scheduled_event_service)

    database_manager = DatabaseManager()

    plugin_lifecycle_manager = PluginLifecycleManager(bolt_app)
    plugin_locator: PluginLocator = PluginLocator(plugin_lifecycle_manager)

    plugin_lifecycle_manager.register_parameter('slack', bolt_app)
    plugin_lifecycle_manager.register_parameter('http', http_event_interface)

    slack_plugin_integration: SlackPluginIntegration = SlackPluginIntegration(bolt_app)
    http_plugin_integration: HttpPluginIntegration = HttpPluginIntegration(http_event_interface, plugin_locator)

    plugin_lifecycle_manager.register_plugin_unregister_callback(slack_plugin_integration.disconnect_plugin)
    plugin_lifecycle_manager.register_plugin_unregister_callback(http_plugin_integration.disconnect_plugin)

    plugin_lifecycle_manager.register_plugin_preregister_callback(http_plugin_integration.initialise_plugin_router)

    plugin_lifecycle_manager.load_plugins()

    http_plugin_integration.finalise_http_setup()

    await database_manager.initialise()

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