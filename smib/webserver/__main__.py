import os
import pickle
from flask import Flask, request
from smib.common.config import WEBSERVER_HOST, WEBSERVER_PORT, WEBSERVER_SECRET_KEY, WEBSOCKET_URL
from smib.common.utils import is_pickleable
from slack_bolt.adapter.flask.handler import to_bolt_request, BoltRequest, to_flask_response, BoltResponse
from websocket import create_connection, WebSocket, ABNF


class WebSocketHandler:
    def __init__(self):
        self.websocket_conn: WebSocket = self.create_websocket_conn()

    @staticmethod
    def create_websocket_conn():
        return create_connection(WEBSOCKET_URL.geturl())

    def check_and_reconnect_websocket_conn(self):
        try:
            self.websocket_conn.send('', ABNF.OPCODE_PING)
        except Exception as e:
            print('Reconnecting websocket')
            self.websocket_conn = self.create_websocket_conn()

    def send_bolt_request(self, flask_request):
        self.websocket_conn.send_binary(pickle.dumps(flask_request))

    def receive_bolt_response(self):
        response_str = self.websocket_conn.recv()
        return pickle.loads(response_str)

    def close_conn(self):
        self.websocket_conn.close()


def generate_request_body(flask_request):
    event_type = f"http_{flask_request.method.lower()}_{flask_request.view_args.get('event')}"
    return {
        'type': 'event_callback',
        'event': {
            "type": event_type,
            "data": flask_request.get_json(silent=True) or {},
            "request": {
                "method": flask_request.method,
                "scheme": flask_request.scheme,
                "url": flask_request.url,
                "headers": dict(filter(lambda item: is_pickleable(item), flask_request.headers))
            }
        }
    }


def generate_bolt_request(flask_request):
    bolt_request: BoltRequest = to_bolt_request(flask_request)
    bolt_request.body = generate_request_body(flask_request)
    return bolt_request


# Instantiate our websocket handler
ws_handler = WebSocketHandler()
app = Flask(__name__)
app.secret_key = WEBSERVER_SECRET_KEY


@app.route('/smib/event/<string:event>')
def smib_event_handler(*args, **kwargs):
    ws_handler.check_and_reconnect_websocket_conn()
    bolt_request: BoltRequest = generate_bolt_request(request)
    ws_handler.send_bolt_request(bolt_request)
    bolt_response: BoltResponse = ws_handler.receive_bolt_response()
    return to_flask_response(bolt_response)


if __name__ == '__main__':
    try:
        app.run(host=WEBSERVER_HOST, port=WEBSERVER_PORT, debug=True)
    finally:
        ws_handler.close_conn()
