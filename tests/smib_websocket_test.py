import websocket
import _thread
import time

from smib.common.config import WEBSOCKET_HOST, WEBSOCKET_PORT

def on_message(ws, message):
    print(f'Got: {message}')

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    print("Opened connection")
    ws.send("Hello World")

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(f"ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    ws.run_forever()