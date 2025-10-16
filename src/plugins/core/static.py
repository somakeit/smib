__display_name__ = "Static Files"
__description__ = "Serves static files from the static folder"
__author__ = "Sam Cork"

import logging
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse
from pydantic import Field

from smib.config import EnvBaseSettings
from smib.config.utils import init_plugin_settings
from smib.events.interfaces.http.http_web_event_interface import WebEventInterface


class StaticFilesPluginSettings(EnvBaseSettings):
    static_files_directory: Path = Field(
        default="static",
        description="Directory where static files are stored and served from"
    )

    model_config = {
        "env_prefix": "SMIB_PLUGIN_STATIC_FILES_"
    }

logger = logging.getLogger(__display_name__)
config = init_plugin_settings(StaticFilesPluginSettings, logger)

def register(web: WebEventInterface):
    resolved_static_directory_path: Path = config.static_files_directory.resolve()
    logger.info(f"Resolved static files directory to {resolved_static_directory_path}")
    if not resolved_static_directory_path.exists():
        logger.debug(f"Creating static files directory at {resolved_static_directory_path}")
        resolved_static_directory_path.mkdir(parents=True)

    logger.info(f"Mounting static files directory at /static")

    # TODO (eventually): Replace this with normal StaticFiles mounting.
    #  This is a workaround for FastAPI issue #10180 (https://github.com/fastapi/fastapi/issues/10180).
    #  For additional context, see the related discussion: https://github.com/fastapi/fastapi/discussions/9070.
    @web.get("/static/{rest_of_path:path}", include_in_schema=False)
    async def static_files(rest_of_path: str):
        file_path = resolved_static_directory_path / rest_of_path
        if not rest_of_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(file_path)