import logging

from injectable import inject
from websocket import create_connection, WebSocket
from smib.webserver.config import WEBSOCKET_URL
import pickle


class WebSocketHandler:

    def __init__(self):
        self.websocket_conn: WebSocket = self.create_websocket_conn()

    @staticmethod
    def create_websocket_conn():
        logger: logging.Logger = inject("logger")
        try:
            url = WEBSOCKET_URL.geturl()
            logger.info(f'Creating websocket connection: {url}')
            return create_connection(url, timeout=5)
        except Exception as e:
            logger.exception(e)

        return None


    def check_and_reconnect_websocket_conn(self):
        logger: logging.Logger = inject("logger")
        try:
            self.websocket_conn.ping()
        except Exception as e:
            logger.info('Reconnecting websocket')
            self.websocket_conn = self.create_websocket_conn()

    def send_bolt_request(self, bolt_request):
        self.websocket_conn.send_binary(pickle.dumps(bolt_request))

    async def receive_bolt_response(self):
        response_str = self.websocket_conn.recv()
        return pickle.loads(response_str)

    def close_conn(self):
        self.websocket_conn.close()
