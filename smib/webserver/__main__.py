from pathlib import Path

from fastapi import FastAPI, Request, APIRouter
from slack_bolt.request import BoltRequest
from slack_bolt.response import BoltResponse
from slack_bolt.adapter.starlette.handler import to_bolt_request, to_starlette_response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from smib.common.config import (
    WEBSERVER_HOST, WEBSERVER_PORT, WEBSERVER_PATH_PREFIX, WEBSERVER_STATIC_DIRECTORY, WEBSERVER_TEMPLATES_DIRECTORY
)
from smib.common.utils import is_pickleable
from smib.webserver.websocket_handler import WebSocketHandler


async def generate_request_body(fastapi_request):
    event_type = f"http_{fastapi_request.method.lower()}_{fastapi_request.path_params.get('event', None)}"
    try:
        json = await fastapi_request.json()
    except Exception as _:
        json = {}
    return {
        'type': 'event_callback',
        'event': {
            "type": event_type,
            "data": json,
            "request": {
                "method": fastapi_request.method,
                "scheme": fastapi_request.url.scheme,
                "base_url": str(fastapi_request.base_url).rstrip('/') + str(fastapi_request.url.path),
                "url": str(fastapi_request.url),
                "parameters": dict(fastapi_request.query_params),
                "headers": dict(filter(lambda item: is_pickleable(item), fastapi_request.headers.items()))
            }
        }
    }


async def generate_bolt_request(fastapi_request: Request):
    body = await fastapi_request.body()
    bolt_request: BoltRequest = to_bolt_request(fastapi_request, body=body)
    bolt_request.body = await generate_request_body(fastapi_request)
    return bolt_request


def create_directories():
    if not WEBSERVER_TEMPLATES_DIRECTORY.exists():
        WEBSERVER_TEMPLATES_DIRECTORY.mkdir()

    if not WEBSERVER_STATIC_DIRECTORY.exists():
        WEBSERVER_STATIC_DIRECTORY.mkdir()


ws_handler = WebSocketHandler()
app = FastAPI()
router = APIRouter(prefix=WEBSERVER_PATH_PREFIX)

create_directories()

router.mount("/static", StaticFiles(directory=WEBSERVER_STATIC_DIRECTORY), name="static")
templates = Jinja2Templates(directory=str(WEBSERVER_TEMPLATES_DIRECTORY))


@router.get('/event/{event}', tags=['SMIB Events'])
@router.post('/event/{event}', tags=['SMIB Events'])
async def smib_event_handler(request: Request, event: str):
    ws_handler.check_and_reconnect_websocket_conn()
    bolt_request: BoltRequest = await generate_bolt_request(request)
    ws_handler.send_bolt_request(bolt_request)
    bolt_response: BoltResponse = await ws_handler.receive_bolt_response()
    return to_starlette_response(bolt_response)


@router.get('/', response_class=HTMLResponse)
async def smib_home(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.exception_handler(404)
async def custom_404_handler(request, __):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


app.include_router(router)


def main(app: FastAPI, ws_handler: WebSocketHandler):
    try:
        import uvicorn
        uvicorn.run(app, host=WEBSERVER_HOST, port=WEBSERVER_PORT)
    finally:
        ws_handler.close_conn()


if __name__ == '__main__':
    main(app, ws_handler)
