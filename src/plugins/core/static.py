__display_name__ = "Static Files"
__description__ = "Serves static files from the static folder"

import logging
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse, Response

from smib.events.interfaces.http_event_interface import HttpEventInterface
from smib.config import config, PACKAGE_ROOT

STATIC_FILES_DIRECTORY: Path = config('STATIC_FILES_DIRECTORY', default='static', cast=Path)

logger = logging.getLogger(__display_name__)

def register(http: HttpEventInterface):
    resolved_static_directory_path: Path = STATIC_FILES_DIRECTORY.resolve()
    logger.info(f"Resolved static files directory to {resolved_static_directory_path}")
    if not resolved_static_directory_path.exists():
        logger.debug(f"Creating static files directory at {resolved_static_directory_path}")
        resolved_static_directory_path.mkdir(parents=True)

    logger.info(f"Mounting static files directory at /static")

    # TODO (eventually): Replace this with normal StaticFiles mounting
    #  That method doesn't currently work due to https://github.com/fastapi/fastapi/issues/10180
    #  More info: https://github.com/fastapi/fastapi/discussions/9070
    @http.get("/static/{rest_of_path:path}", include_in_schema=False)
    async def static_files(rest_of_path: str):
        file_path = resolved_static_directory_path / rest_of_path
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(file_path)