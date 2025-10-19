from functools import cache

from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html
from starlette.responses import JSONResponse

from smib.config import project
from smib.db.manager import DatabaseManager
from smib.events.interfaces.http.http_web_event_interface import WebEventInterface
from smib.utilities import split_camel_case
from . import FAVICON_URL, LOGO_URL


def register(database: DatabaseManager, web: WebEventInterface):

    cached_openapi_schema: dict | None = None

    @web.get("/database/docs")
    async def get_database_docs():
        return get_redoc_html(openapi_url="/database/openapi.json", title=f"{project.display_name} - Database Docs", redoc_favicon_url=FAVICON_URL)

    @web.get("/database/openapi.json", response_class=JSONResponse)
    async def get_database_schema():
        nonlocal cached_openapi_schema
        if not cached_openapi_schema:
            cached_openapi_schema = get_openapi_schema()
        return JSONResponse(cached_openapi_schema)

    @cache
    def get_openapi_schema():
        dummy_app = FastAPI(
            title=f"{project.display_name} - Database Docs",
            version=project.version,
            description="This is the database schema documentation. Database is a Mongo DB instance.",
            openapi_url="/database/openapi.json",
            docs_url=None,
            redoc_url=None,
        )

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
        openapi["info"]["x-logo"] = {
            "url": LOGO_URL
        }

        return openapi

