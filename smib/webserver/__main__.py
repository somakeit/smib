import re
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, APIRouter
from injectable import load_injection_container, inject
from slack_bolt.request import BoltRequest
from slack_bolt.response import BoltResponse
from slack_bolt.adapter.starlette.handler import to_bolt_request, to_starlette_response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from smib.webserver.config import (
    WEBSERVER_HOST, WEBSERVER_PORT, WEBSERVER_PATH_PREFIX, WEBSERVER_STATIC_DIRECTORY, WEBSERVER_TEMPLATES_DIRECTORY,
    ROOT_DIRECTORY, APPLICATION_NAME
)
from smib.common.utils import is_pickleable, get_version
from smib.webserver.websocket_handler import WebSocketHandler

from smib.common.logging_.setup import setup_logging, read_logging_json

setup_logging()

load_injection_container(ROOT_DIRECTORY / "common")
load_injection_container(ROOT_DIRECTORY / "webserver")


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
                "headers": dict(filter(lambda item: is_pickleable(item), fastapi_request.headers.items())),
                "ip": fastapi_request.scope["client"][0]
            }
        }
    }


async def generate_bolt_request(fastapi_request: Request):
    body = await fastapi_request.body()
    bolt_request: BoltRequest = to_bolt_request(fastapi_request, body=body)
    bolt_request.body = await generate_request_body(fastapi_request)
    return bolt_request


def create_directories():
    logger = inject("logger")
    logger.debug(f"Resolved Webserver Template Directory to: {WEBSERVER_TEMPLATES_DIRECTORY}")
    if not WEBSERVER_TEMPLATES_DIRECTORY.exists():
        logger.info(f"Creating webserver templates directory: {WEBSERVER_TEMPLATES_DIRECTORY}")
        WEBSERVER_TEMPLATES_DIRECTORY.mkdir()

    logger.debug(f"Resolved Webserver Static Directory to: {WEBSERVER_STATIC_DIRECTORY}")
    if not WEBSERVER_STATIC_DIRECTORY.exists():
        logger.info(f"Creating webserver static directory: {WEBSERVER_STATIC_DIRECTORY}")
        WEBSERVER_STATIC_DIRECTORY.mkdir()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    logger = inject("logger")
    logger.info(f"Webserver started")

    yield

    # Clean up the ML models and release the resources
    logger.info(f"Webserver Stopping")


def get_readme() -> str:
    description = None
    description_path = Path(__file__).parent / "README.md"
    if description_path.exists() and description_path.is_file():
        with open(description_path) as readme:
            description = readme.read()

    return description


def get_readme_without_title() -> str:
    description = get_readme()
    description = re.sub(r"#.*\n", "", description, 1)
    return description


def get_title() -> str:
    title = None
    description = get_readme()

    return re.findall(r"#(.*)", description)[0]


event_responses = {
    404: {"description": "Not Processed"},
    418: {"description": "Unhandled Exception"}
}

ws_handler = WebSocketHandler()

app = FastAPI(lifespan=lifespan, title=get_title(), version=get_version(), description=get_readme_without_title(), redoc_url=None)
smib_router = APIRouter(prefix=WEBSERVER_PATH_PREFIX)
event_router = APIRouter(prefix='/event', tags=['S.M.I.B. Events'], responses=event_responses)

create_directories()

app.mount("/static", StaticFiles(directory=WEBSERVER_STATIC_DIRECTORY), name="static")
templates = Jinja2Templates(directory=str(WEBSERVER_TEMPLATES_DIRECTORY))


@event_router.get('/{event}', name="S.M.I.B. GET Event")
@event_router.post('/{event}', name="S.M.I.B. POST Event")
@event_router.put('/{event}', name="S.M.I.B. PUT Event")
async def smib_event_handler(request: Request, event: str):
    logger = inject("logger")

    ws_handler.check_and_reconnect_websocket_conn()

    device_ip, port = request.scope["client"]
    device_hostname = request.headers.get("Device-Hostname", None)

    logger.info(f"Received event {event} from {device_hostname or device_ip}{f' ({device_ip})' if device_hostname else ''}")

    bolt_request: BoltRequest = await generate_bolt_request(request)

    logger.debug(f"Request: {request.__dict__}")
    logger.debug(f"Bolt Request: {bolt_request.__dict__}")

    ws_handler.send_bolt_request(bolt_request)
    bolt_response: BoltResponse = await ws_handler.receive_bolt_response()
    response = to_starlette_response(bolt_response)

    logger.debug(f"Bolt Response:{bolt_response.__dict__}")
    logger.debug(f"Response: {response.__dict__}")
    return response


@app.exception_handler(404)
async def custom_404_handler(request, __):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


smib_router.include_router(event_router)
app.include_router(smib_router)


def main(app: FastAPI, ws_handler: WebSocketHandler):
    logger = inject("logger")
    try:
        import uvicorn
        logger.info(f"Starting WebServer v{get_version()}")
        uvicorn.run(app, host=WEBSERVER_HOST, port=WEBSERVER_PORT, log_config=read_logging_json(), headers=[("server", APPLICATION_NAME)])
    except KeyboardInterrupt:
        ...
    finally:
        logger.info(f"Stopping WebsocketHandler")
        ws_handler.close_conn()

        logger.info(f"Webserver Stopped")


if __name__ == '__main__':
    main(app, ws_handler)
