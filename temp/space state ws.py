import asyncio
import json

import websockets


async def listen():
    uri = "ws://localhost:8080/ws/space/state"
    headers = {
        "Origin": "http://localhost:8080"
    }
    async with websockets.connect(uri, additional_headers=headers) as websocket:
        print("Connected to WebSocket")
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                print("Received:", data)
            except websockets.ConnectionClosed:
                print("Connection closed")
                break

asyncio.run(listen())
