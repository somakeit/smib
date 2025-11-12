from functools import cache
from pathlib import Path

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.responses import JSONResponse

from smib.config import project
from smib.db.manager import DatabaseManager
from smib.events.interfaces.http.http_web_event_interface import WebEventInterface
from smib.utilities import split_camel_case
from smib.utilities.beanie_ import get_model_indexes
from . import FAVICON_URL, LOGO_URL

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def register(database: DatabaseManager, web: WebEventInterface):

    cached_openapi_schema: dict | None = None

    @web.get("/database/docs")
    async def get_database_docs(fastapi_request: Request,):
        response = templates.TemplateResponse(
            request=fastapi_request,
            name="custom_database_redoc.html",
            context={
                "request": fastapi_request,
                "openapi_url": "/database/openapi.json",
                "title": f"{project.display_name} - Database Docs",
                "favicon_url": FAVICON_URL
            }
        )
        return response

    @web.get("/database/openapi.json", response_class=JSONResponse)
    async def get_database_schema():
        nonlocal cached_openapi_schema
        if not cached_openapi_schema:
            cached_openapi_schema = get_openapi_schema()
        return JSONResponse(cached_openapi_schema)

    @cache
    def get_openapi_schema():
        dummy_app = create_dummy_app()
        models = database.get_all_document_models()
        add_dummy_routes(dummy_app, models)

        openapi = dummy_app.openapi()
        del dummy_app

        openapi['paths'] = {}

        tags = generate_tags(models)
        openapi['tags'] = tags
        openapi['x-tagGroups'] = generate_tag_groups(tags)

        add_openapi_metadata(openapi)
        remove_required(openapi)
        add_model_metadata(openapi, models)

        return openapi



    def add_openapi_metadata(openapi: dict):
        """Add logo and external docs to the OpenAPI schema."""
        openapi["info"]["x-logo"] = {
            "url": LOGO_URL,
            "altText": "So Make It Logo",
            "href": "https://github.com/somakeit/smib"
        }
        openapi["externalDocs"] = {
            "description": f"{project.display_name} - API Docs",
            "url": web.service.fastapi_app.root_path.rstrip('/') + "/api/docs",
        }

def add_model_metadata(openapi: dict, models: list):
    """Add model metadata to the OpenAPI schema."""
    for model in models:
        openapi["components"]["schemas"][model.__name__]['x-isDatabaseModel'] = True
        openapi["components"]["schemas"][model.__name__]['x-collectionName'] = model.get_collection_name()
        openapi["components"]["schemas"][model.__name__]['x-indexes'] = [idx.model_dump() for idx in get_model_indexes(model)]

def create_dummy_app() -> FastAPI:
    """Create a dummy FastAPI app for generating OpenAPI schema."""
    return FastAPI(
        title=f"{project.display_name} - Database Docs",
        version=str(project.version),
        description="This is the database schema documentation. The database is a Mongo DB instance.",
        openapi_url="/database/openapi.json",
        docs_url=None,
        redoc_url=None,
    )


def add_dummy_routes(app: FastAPI, models: list):
    """Add temporary routes to generate the schema for each model."""
    for model in models:
        app.add_api_route(
            f"/{model.get_collection_name()}",
            lambda: model,
            methods=["GET"],
            response_model=model
        )


def generate_tags(models: list) -> list:
    """Generate OpenAPI tags with HTML descriptions for models."""
    description_template = templates.get_template("database_collection_schema.html")
    tags = []
    for model in sorted(models, key=lambda m: m.__name__):
        html = description_template.render(
            collection=model.get_collection_name(),
            description=model.__doc__,
            schema_ref_name=model.__name__
        )
        tag = {
            "name": model.get_collection_name(),
            "x-displayName": " ".join(split_camel_case(model.__name__)),
            "description": html
        }
        tags.append(tag)
    return tags


def generate_tag_groups(tags: list) -> list:
    """Generate OpenAPI x-tagGroups."""
    return [{
        "name": "Database Models",
        "tags": [tag["name"] for tag in tags]
    }]

def remove_required(schema: dict):
    """
    Recursively remove all 'required' keys from an OpenAPI schema dict.
    """

    def recurse(obj):
        if isinstance(obj, dict):
            obj.pop("required", None)  # remove required if present
            for k, v in obj.items():
                recurse(v)
        elif isinstance(obj, list):
            for item in obj:
                recurse(item)

    recurse(schema)
