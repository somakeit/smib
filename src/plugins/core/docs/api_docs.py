from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

from smib.config import project
from smib.events.interfaces.http.http_web_event_interface import WebEventInterface
from . import FAVICON_URL, LOGO_URL


def register(web: WebEventInterface):
    fastapi_app: FastAPI = web.service.fastapi_app
    app_title = fastapi_app.title

    web.service.fastapi_app.redoc_url = None
    web.service.fastapi_app.docs_url = None

    remove_route_by_name(fastapi_app, "swagger_ui_html")
    remove_route_by_name(fastapi_app, "swagger_ui_redirect")
    remove_route_by_name(fastapi_app, "redoc_html")

    @web.get("/api/docs")
    async def overridden_swagger():
        return get_swagger_ui_html(openapi_url=fastapi_app.root_path.rstrip('/') + "/openapi.json", title=f"{app_title} - Swagger UI", swagger_favicon_url=FAVICON_URL)

    @web.get("/api/redoc")
    async def overridden_redoc():
        return get_redoc_html(openapi_url=fastapi_app.root_path.rstrip('/') + "/openapi.json", title=f"{app_title} - ReDoc", redoc_favicon_url=FAVICON_URL)

    def overridden_openapi():
        if fastapi_app.openapi_schema:
            return fastapi_app.openapi_schema
        openapi_schema = get_openapi(
            title=project.display_name,
            version=project.version,
            description=project.description,
            routes=fastapi_app.routes,
            tags=fastapi_app.openapi_tags
        )
        openapi_schema["info"]["x-logo"] = {
            "url": LOGO_URL,
            "altText": "So Make It Logo",
            "href": "https://github.com/somakeit/smib"
        }
        openapi_schema["externalDocs"] = {
            "description": f"{project.display_name} - Database Docs",
            "url": fastapi_app.root_path.rstrip('/') + "/database/docs",
        }
        fastapi_app.openapi_schema = openapi_schema
        return fastapi_app.openapi_schema

    fastapi_app.openapi = overridden_openapi

def remove_route_by_name(app, route_name: str):
    routes_to_remove = [route for route in app.routes if route.name == route_name]
    for route in routes_to_remove:
        app.routes.remove(route)