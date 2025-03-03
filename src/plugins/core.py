__display_name__ = "Core"
__description__ = "A plugin to provide core functionality"
__author__ = "sam57719"

from smib.events.interfaces.http_event_interface import HttpEventInterface


def register(http: HttpEventInterface):
    http.current_router.prefix = '/core'

    http.add_openapi_tags([{
        "name": "Monitoring",
        "description": "Monitoring endpoints"
    }])

    @http.get("/health", tags=["Monitoring"])
    async def health():
        """ Check the health of the bot """
        return {"ok": True}