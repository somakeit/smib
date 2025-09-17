__display_name__ = "API Docs"
__description__ = "Plugin to override the default API docs, allowing for customisation"
__author__ = "Sam Cork"

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

from smib.events.interfaces.http.http_web_event_interface import WebEventInterface

FAVICON_URL = "https://members.somakeit.org.uk/images/somakeit/favicon.ico"

def register(web: WebEventInterface):
    fastapi_app: FastAPI = web.service.fastapi_app
    app_title = fastapi_app.title

    web.service.fastapi_app.redoc_url = None
    web.service.fastapi_app.docs_url = None

    remove_route_by_name(fastapi_app, "swagger_ui_html")
    remove_route_by_name(fastapi_app, "swagger_ui_redirect")
    remove_route_by_name(fastapi_app, "redoc_html")

    @web.get("/api/docs", include_in_schema=False)
    async def overridden_swagger():
        return get_swagger_ui_html(openapi_url=fastapi_app.root_path.rstrip('/') + "/openapi.json", title=f"{app_title} - Swagger UI", swagger_favicon_url=FAVICON_URL)

    @web.get("/api/redoc", include_in_schema=False)
    async def overridden_redoc():
        return get_redoc_html(openapi_url=fastapi_app.root_path.rstrip('/') + "/openapi.json", title=f"{app_title} - ReDoc", redoc_favicon_url=FAVICON_URL)

def remove_route_by_name(app, route_name: str):
    routes_to_remove = [route for route in app.routes if route.name == route_name]
    for route in routes_to_remove:
        app.routes.remove(route)