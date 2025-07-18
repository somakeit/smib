import asyncio
import logging
from asyncio import CancelledError

from pymongo.errors import PyMongoError
from slack_bolt.app.async_app import AsyncApp

from smib.config import SLACK_BOT_TOKEN, PACKAGE_DISPLAY_NAME, SIGNING_SECRET
from smib.db.manager import DatabaseManager
from smib.error_handler import slack_bolt_error_handler
from smib.events.handlers.http_event_handler import HttpEventHandler
from smib.events.handlers.scheduled_event_handler import ScheduledEventHandler
from smib.events.interfaces.http_event_interface import HttpEventInterface
from smib.events.interfaces.scheduled_event_interface import ScheduledEventInterface
from smib.events.services import EventServiceManager
from smib.events.services.http_event_service import HttpEventService
from smib.events.services.scheduled_event_service import ScheduledEventService
from smib.events.services.slack_event_service import SlackEventService
from smib.logging_ import initialise_logging
from smib.plugins.integrations.database_plugin_integration import DatabasePluginIntegration
from smib.plugins.integrations.http_plugin_integration import HttpPluginIntegration
from smib.plugins.integrations.scheduled_plugin_integration import ScheduledPluginIntegration
from smib.plugins.integrations.slack_plugin_integration import SlackPluginIntegration
from smib.plugins.lifecycle_manager import PluginLifecycleManager
from smib.plugins.loaders import create_default_plugin_loader
from smib.signal_handler import register_signal_handlers, get_shutdown_event
from smib.utilities.environment import is_running_in_docker


async def main():
    initialise_logging()
    register_signal_handlers()
    shutdown_event = get_shutdown_event()

    bolt_app = AsyncApp(
        name=PACKAGE_DISPLAY_NAME,
        token=SLACK_BOT_TOKEN,
        signing_secret=SIGNING_SECRET,
        raise_error_for_unhandled_request=True,
        process_before_response=True,
        logger=logging.getLogger("slack_bolt.AsyncApp")
    )
    bolt_app.error(slack_bolt_error_handler)

    logger = logging.getLogger(__name__)
    logger.info(f"Running in docker: {is_running_in_docker()}")

    # Most of the slack stuff is handled by the SlackBolt Framework
    slack_event_service = SlackEventService(bolt_app)

    # HTTP Service
    http_event_service = HttpEventService()
    http_event_handler = HttpEventHandler(bolt_app)
    http_event_interface = HttpEventInterface(bolt_app, http_event_handler, http_event_service)

    # Scheduled Job Service
    scheduled_event_service = ScheduledEventService()
    scheduled_event_handler = ScheduledEventHandler(bolt_app)
    scheduled_event_interface = ScheduledEventInterface(bolt_app, scheduled_event_handler, scheduled_event_service)

    # Register Services
    event_service_manager = EventServiceManager()
    event_service_manager.register(slack_event_service)
    event_service_manager.register(http_event_service)
    event_service_manager.register(scheduled_event_service)

    database_manager = DatabaseManager()

    # Plugin Stuff
    plugin_loader = create_default_plugin_loader()
    plugin_lifecycle_manager = PluginLifecycleManager(bolt_app, plugin_loader)

    plugin_lifecycle_manager.register_parameter('slack', bolt_app)
    plugin_lifecycle_manager.register_parameter('http', http_event_interface)
    plugin_lifecycle_manager.register_parameter('schedule', scheduled_event_interface)
    plugin_lifecycle_manager.register_parameter('database', database_manager)

    # Plugin integrations
    slack_plugin_integration: SlackPluginIntegration = SlackPluginIntegration(bolt_app)
    http_plugin_integration: HttpPluginIntegration = HttpPluginIntegration(http_event_interface)
    scheduled_plugin_integration: ScheduledPluginIntegration = ScheduledPluginIntegration(scheduled_event_interface)
    database_plugin_integration: DatabasePluginIntegration = DatabasePluginIntegration(plugin_lifecycle_manager)

    # Plugin lifecycle callbacks
    plugin_lifecycle_manager.register_plugin_unregister_callback(slack_plugin_integration.disconnect_plugin)
    plugin_lifecycle_manager.register_plugin_unregister_callback(http_plugin_integration.disconnect_plugin)
    plugin_lifecycle_manager.register_plugin_unregister_callback(scheduled_plugin_integration.disconnect_plugin)

    plugin_lifecycle_manager.register_plugin_preregister_callback(http_plugin_integration.initialise_plugin_router)
    plugin_lifecycle_manager.register_plugin_postregister_callback(http_plugin_integration.remove_router_if_unused)

    plugin_lifecycle_manager.load_plugins()

    http_plugin_integration.finalise_http_setup()

    database_manager.register_document_filter(database_plugin_integration.filter_valid_plugins)

    try:
        # Initialise database
        await database_manager.initialise()

        # Start services and wait for them to be ready
        services_task = asyncio.create_task(event_service_manager.start_all())
        await asyncio.sleep(1)  # Give services time to initialize
        
        shutdown_task = asyncio.create_task(shutdown_event.wait())
        
        try:
            # Wait for shutdown signal
            await shutdown_task
        finally:
            # First cancel the services task
            services_task.cancel()
            try:
                await services_task
            except asyncio.CancelledError:
                logger.info("Services shutdown gracefully")
                
            # Then stop all services properly
            await event_service_manager.stop_all()
            
    except (KeyboardInterrupt, CancelledError, SystemExit) as e:
        logger.info(f"Received termination: {repr(e)}")
    except PyMongoError as e:
        # Already handled in DatabaseManager
        pass
    except Exception as e:
        logger.exception(f"Unexpected exception: {repr(e)}", exc_info=True)
    finally:
        # Always unload plugins, regardless of how we got here
        plugin_lifecycle_manager.unload_plugins()

    logger.info("Shutdown complete")

if __name__ == '__main__':
    asyncio.run(main())