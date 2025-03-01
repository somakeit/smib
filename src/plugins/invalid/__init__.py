from slack_bolt.app.async_app import AsyncApp

from smib.events.interfaces.http_event_interface import HttpEventInterface

from .routes import load_routes


def register(slack: AsyncApp, http: HttpEventInterface):
    @slack.event("app_mention")
    async def handle_app_mentions(body, say, logger):
        pass

    @slack.event("message")
    async def handle_message(body, say, logger):
        pass

    @slack.event("app_uninstalled")
    async def handle_app_uninstalled(body, say, logger):
        pass

    @slack.event("app_home_opened")
    async def handle_app_home_opened(body, say, logger):
        pass

    load_routes(http)