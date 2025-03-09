import logging
import pprint
from logging import Logger

from fastapi import HTTPException
from fastapi.exception_handlers import http_exception_handler
from slack_bolt import BoltResponse
from slack_bolt.error import BoltUnhandledRequestError
from slack_bolt.listener.async_listener_error_handler import AsyncDefaultListenerErrorHandler
from slack_bolt.request.async_request import AsyncBoltRequest

from smib.events.handlers import BoltRequestMode
from smib.events.responses.http_bolt_response import HttpBoltResponse

default_error_handler_logger = logging.getLogger(AsyncDefaultListenerErrorHandler.__name__)
default_error_handler = AsyncDefaultListenerErrorHandler(default_error_handler_logger)

async def error_handler(error: Exception | HTTPException, request: AsyncBoltRequest, body: dict, response: BoltResponse, logger: Logger):

    match request.mode:
        case BoltRequestMode.SOCKET_MODE if isinstance(error, BoltUnhandledRequestError):
            return await default_error_handler.handle(error, request, response)
        case BoltRequestMode.HTTP if isinstance(error, HTTPException):
            # noinspection PyTypeChecker
            response = await http_exception_handler(None, error)
            return HttpBoltResponse(status=response.status_code, body=response.body, headers=dict(response.headers), fastapi_response=response)
        case _:
            logger.info(f'Request mode: {request.mode}')
            logger.warning(pprint.pformat(body, sort_dicts=False), exc_info=error)
            # logger.warning(f'Failed to execute a request ({error})')