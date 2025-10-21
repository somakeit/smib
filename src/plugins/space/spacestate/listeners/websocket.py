import logging

from starlette.websockets import WebSocket, WebSocketDisconnect

from smib.events.interfaces.websocket_event_interface import WebsocketEventInterface
from ..common import get_space_state_from_db
from ..models import SpaceStateEnum

clients = set()
logger = logging.getLogger("Space State Websocket")

def register(ws: WebsocketEventInterface):

    @ws.websocket('/space/state')
    async def handle_space_state_connections(websocket: WebSocket):
        await websocket.accept()
        clients.add(websocket)
        logger.info(f"Client connected: {websocket.client.host}")

        try:
            # Send initial state
            state = await get_space_state_from_db()
            await websocket.send_json(state.model_dump())

            # Listen for messages (or just keep connection alive)
            while True:
                try:
                    await websocket.receive()
                except WebSocketDisconnect:
                    break
                except RuntimeError as e:
                    # Happens if connection closed unexpectedly
                    logger.debug(f"Runtime error on receive: {e}")
                    break

        finally:
            clients.discard(websocket)
            try:
                await websocket.close()
            except Exception:
                pass  # Already closed
            logger.debug(f"Cleaned up connection for: {websocket.client.host}")


async def inform_websocket_clients_of_space_state_change(new_state: SpaceStateEnum):
    state_json = {"open": new_state == SpaceStateEnum.OPEN}
    for client in clients.copy():
        try:
            await client.send_json(state_json)
            logger.info(f"Sent space state to client: {client.client.host}")
        except Exception:
            clients.discard(client)
            logger.info(f"Client disconnected: {client.client.host}")