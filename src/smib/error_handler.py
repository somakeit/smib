import logging
import pprint
from enum import StrEnum
from http import HTTPStatus
from logging import Logger

from slack_bolt import BoltResponse
from slack_bolt.error import BoltUnhandledRequestError
from slack_bolt.listener.async_listener_error_handler import AsyncDefaultListenerErrorHandler
from slack_bolt.request.async_request import AsyncBoltRequest

class BoltRequestMode(StrEnum):
    SOCKET_MODE = 'socket_mode'
    HTTP = 'http_request'

default_error_handler_logger = logging.getLogger(AsyncDefaultListenerErrorHandler.__name__)
default_error_handler = AsyncDefaultListenerErrorHandler(default_error_handler_logger)

async def error_handler(error: Exception, request: AsyncBoltRequest, body: dict, response: BoltResponse, logger: Logger):

    match request.mode:
        case BoltRequestMode.SOCKET_MODE if isinstance(error, BoltUnhandledRequestError):
            return await default_error_handler.handle(error, request, response)
        case _:
            logger.info(f'Request mode: {request.mode}')
            logger.warning(pprint.pformat(body, sort_dicts=False), exc_info=error)