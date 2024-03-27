import pickle

from fastapi import FastAPI, Request
from slack_bolt.request import BoltRequest
from slack_bolt.adapter.starlette.handler import to_bolt_request, to_starlette_response
from smib.common.config import WEBSERVER_HOST, WEBSERVER_PORT, WEBSERVER_SECRET_KEY, WEBSOCKET_URL
from smib.common.utils import is_pickleable
from websocket import create_connection, WebSocket


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


async def generate_request_body(fastapi_request):
    event_type = f"http_{fastapi_request.method.lower()}_{fastapi_request.path_params.get('event', None)}"
    try:
        json = await fastapi_request.json()
    except Exception as e:
        json = {}
    return {
        'type': 'event_callback',
        'event': {
            "type": event_type,
            "data":  json,
            "request": {
                "method": fastapi_request.method,
                "scheme": fastapi_request.url.scheme,
                "url": str(fastapi_request.url),
                "headers": dict(filter(lambda item: is_pickleable(item), fastapi_request.headers.items()))
            }
        }
    }


async def generate_bolt_request(fastapi_request: Request):
    body = await fastapi_request.body()
    bolt_request: BoltRequest = to_bolt_request(fastapi_request, body=body)
    bolt_request.body = await generate_request_body(fastapi_request)
    return bolt_request


def main():
    ws_handler = WebSocketHandler()
    app = FastAPI()

    @app.get('/smib/event/{event}', tags=['SMIB Events'])
    async def smib_event_handler(request: Request, event: str):
        ws_handler.check_and_reconnect_websocket_conn()
        bolt_request: BoltRequest = await generate_bolt_request(request)
        ws_handler.send_bolt_request(bolt_request)
        bolt_response = await ws_handler.receive_bolt_response()
        return to_starlette_response(bolt_response)

    try:
        import uvicorn
        uvicorn.run(app, host=WEBSERVER_HOST, port=WEBSERVER_PORT)
    finally:
        ws_handler.close_conn()


if __name__ == '__main__':
    main()
