import threading
from smib.common.config import WEBSOCKET_HOST, WEBSOCKET_PORT
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket


class SimpleServer(WebSocket):

    def handleMessage(self):
        print(f"Received message: {self.data}")
        response = f"Hello Client, your message was: {self.data}"
        self.sendMessage(response)

    def handleConnected(self):
        print(f"{self.address} connected")

    def handleClose(self):
        print(f"{self.address} closed")


server = SimpleWebSocketServer(WEBSOCKET_HOST, int(WEBSOCKET_PORT), SimpleServer)
threading.Thread(target=server.serveforever).start()
