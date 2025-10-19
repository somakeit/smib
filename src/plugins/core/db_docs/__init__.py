__display_name__ = "Database Docs"
__description__ = "Plugin to provide database docs"
__author__ = "Sam Cork"

import logging

from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html
from starlette.responses import JSONResponse

from smib.db.manager import DatabaseManager
from smib.events.interfaces.http.http_web_event_interface import WebEventInterface
from smib.utilities import split_camel_case

logger = logging.getLogger(__display_name__)

def register(database: DatabaseManager, web: WebEventInterface):

    @web.get("/database/docs")
    async def get_database_docs():
        return get_redoc_html(openapi_url="/database/openapi.json", title="Database Docs")

    @web.get("/database/openapi.json", response_class=JSONResponse)
    async def get_database_schema():
        dummy_app = FastAPI()

        # Get all database models
        models = database.get_all_document_models()
        for model in models:
            dummy_app.add_api_route(f"/{model.get_collection_name()}", lambda: model, methods=["GET"], response_model=model)

        openapi = dummy_app.openapi()
        del dummy_app

        openapi['paths'] = {}

        tags = [
            {
                "name": " ".join(split_camel_case(model.__name__)),
                "x-displayName": " ".join(split_camel_case(model.__name__)),
                "description": f"<div class=\"collection\"><strong>Mongo DB Collection:</strong> {model.get_collection_name()}</div>\n"
                               f"<SchemaDefinition schemaRef=\"#/components/schemas/{model.__name__}\"/>"
            }
            for model in sorted(models, key=lambda m: m.__name__)
        ]

        x_tag_groups = [
            {
                "name": "Database Models",
                "tags": [tag["name"] for tag in tags]
            }
        ]

        openapi['tags'] = tags
        openapi['x-tagGroups'] = x_tag_groups

        return JSONResponse(openapi)

