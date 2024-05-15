import socket

from simple_websocket_server import WebSocketServer, WebSocket
from smib.slack.config import WEBSOCKET_HOST, WEBSOCKET_PORT, WEBSOCKET_ALLOWED_HOSTS
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

        hostname = None
        hostname_ip = None
        address = self.address[0]

        try:
            raw_hostname = socket.gethostbyaddr(address)
            logger.debug(f"{raw_hostname}")

            hostname = raw_hostname[0]
            hostname_ip = socket.gethostbyname(hostname)
        except socket.error:
            logger.debug(f'Unable to resolve address {address} to ip address')
        else:
            logger.debug(f'Address {address} resolved to hostname {hostname}')

        if {address, hostname, hostname_ip}.intersection(set(WEBSOCKET_ALLOWED_HOSTS)):
            return

        logger.warning(f"Connection from {self.address} is {NOT_AUTHORIZED}")
        self.close(reason=NOT_AUTHORIZED)

    def handle_close(self):
        logger: logging.Logger = inject("logger")
        logger.info(f"{self.address} closed")


@injectable_factory(WebSocketServer, singleton=True, qualifier="WebSocketServer")
def get_server():
    logger: logging.Logger = inject("logger")
    try:
        logger.info(f"Binding Websocket Server: 0.0.0.0:{WEBSOCKET_PORT}")
        logger.info(f"Access Websocket Server: {WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
        return WebSocketServer("0.0.0.0", WEBSOCKET_PORT, SlackExternalWebsocketHandler)
    except Exception as e:
        logger.exception(e)
    return None


def start_server(server: WebSocketServer):
    logger: logging.Logger = inject("logger")
    if server is not None:
        logger.info(f"Starting WebSocketServer")
        try:
            server.serve_forever()
        except Exception as e:
            logger.exception(e, exc_info=False)
    else:
        logger.warning('Unable to start WebSocketServer')


def start_threaded_server():
    server_thread = Thread(target=start_server, args=(inject(WebSocketServer),))
    server_thread.daemon = True
    server_thread.start()
    return server_thread


if __name__ == '__main__':
    load_injection_container()
    start_server(inject(WebSocketServer))
