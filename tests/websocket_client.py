import pickle
import threading
from websocket import create_connection
from smib.common.config import WEBSOCKET_HOST, WEBSOCKET_PORT
from slack_bolt.adapter.flask.handler import BoltRequest


def client():
    ws = create_connection(f"ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
    print("Sending 'Hello, Server'...")
    ws.send_binary(pickle.dumps(BoltRequest(body='')))
    print("Sent")
    print("Receiving...")
    result = ws.recv()
    print(f"Received '{pickle.loads(result)}'")
    ws.close()


threading.Thread(target=client).start()
