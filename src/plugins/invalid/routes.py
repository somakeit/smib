from slack_bolt import BoltResponse

from smib.events.interfaces.http_event_interface import HttpEventInterface


def load_routes(http: HttpEventInterface):
    @http.get("/invalid")
    async def invalid():
        return BoltResponse(status=418)