from simple_websocket_server import WebSocketServer, WebSocket
from smib.common.config import WEBSOCKET_HOST, WEBSOCKET_PORT, WEBSOCKET_ALLOWED_HOSTS
from smib.common.utils import log_error
from injectable import injectable_factory, Autowired, load_injection_container, autowired, inject
from slack_bolt.adapter.flask.handler import BoltRequest, BoltResponse
from smib.slack.custom_app import CustomApp as App
from threading import Thread
import pickle
import logging

from http import HTTPStatus


NOT_AUTHORIZED = 'not_authorized'


class SlackExternalWebsocketHandler(WebSocket):

    @log_error
    def handle(self):
        logger: logging.Logger = inject("logger")
        assert isinstance(self.data, bytes) or isinstance(self.data, bytearray), 'Not bytes'
        assert isinstance(bolt_request := pickle.loads(self.data), BoltRequest), 'Not a BoltRequest'
        assert isinstance(slack_app := inject("SlackApp"), App), 'No slack app'

        bolt_request: BoltRequest
        slack_app: App

        event_type: str = bolt_request.body.get('event').get('type')
        logger.debug(f"Received event: {event_type}")

        bolt_response: BoltResponse = slack_app.dispatch(bolt_request)
        self.send_message(pickle.dumps(bolt_response))

        http_status: HTTPStatus = HTTPStatus(bolt_response.status)
        logger.debug(f"Sent status: {bolt_response.status} - {http_status.name}: {http_status.description}")

    def connected(self):
        logger: logging.Logger = inject("logger")
        logger.info(f"{self.address} connected")
        if self.address[0] in WEBSOCKET_ALLOWED_HOSTS:
            return

        logger.warning(f"Connection from {self.address} is {NOT_AUTHORIZED}")
        self.close(reason=NOT_AUTHORIZED)

    def handle_close(self):
        logger: logging.Logger = inject("logger")
        logger.info(f"{self.address} closed")


@injectable_factory(WebSocketServer, singleton=True)
def get_server():
    logger: logging.Logger = inject("logger")
    try:
        return WebSocketServer(WEBSOCKET_HOST, WEBSOCKET_PORT, SlackExternalWebsocketHandler)
    except Exception as e:
        logger.exception(e)
    return None


@autowired
def start_server(server: Autowired(WebSocketServer)):
    logger: logging.Logger = inject("logger")
    if server is not None:
        logger.info(f"Starting WebSocketServer")
        server.serve_forever()
    else:
        logger.warning('Unable to start WebSocketServer')


def start_threaded_server():
    server_thread = Thread(target=start_server)
    server_thread.start()
    return server_thread


if __name__ == '__main__':
    load_injection_container()
    start_server()
