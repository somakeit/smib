from websocket import create_connection, WebSocket
from smib.common.config import WEBSOCKET_URL
import pickle


class WebSocketHandler:
    def __init__(self):
        self.websocket_conn: WebSocket = self.create_websocket_conn()

    @staticmethod
    def create_websocket_conn():
        return create_connection(WEBSOCKET_URL.geturl())

    def check_and_reconnect_websocket_conn(self):
        try:
            self.websocket_conn.ping()
        except Exception as e:
            print('Reconnecting websocket')
            self.websocket_conn = self.create_websocket_conn()

    def send_bolt_request(self, bolt_request):
        self.websocket_conn.send_binary(pickle.dumps(bolt_request))

    async def receive_bolt_response(self):
        response_str = self.websocket_conn.recv()
        return pickle.loads(response_str)

    def close_conn(self):
        self.websocket_conn.close()
