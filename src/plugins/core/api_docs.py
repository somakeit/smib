__display_name__ = "API Docs"
__description__ = "Plugin to override the default API docs, allowing for customisation"

from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

from smib.events.interfaces.http_event_interface import HttpEventInterface

FAVICON_URL = "https://members.somakeit.org.uk/images/somakeit/favicon.ico"

def register(http: HttpEventInterface):
    app_title = http.service.fastapi_app.title

    http.service.fastapi_app.redoc_url = None
    http.service.fastapi_app.docs_url = None

    remove_route_by_name(http.service.fastapi_app, "swagger_ui_html")
    remove_route_by_name(http.service.fastapi_app, "redoc_html")
    remove_route_by_name(http.service.fastapi_app, "swagger_ui_redirect")

    @http.get("/docs", include_in_schema=False)
    async def overridden_swagger():
        return get_swagger_ui_html(openapi_url="/openapi.json", title=f"{app_title} - Swagger UI", swagger_favicon_url=FAVICON_URL)

    @http.get("/redoc", include_in_schema=False)
    async def overridden_redoc():
        return get_redoc_html(openapi_url="/openapi.json", title=f"{app_title} - ReDoc", redoc_favicon_url=FAVICON_URL)

def remove_route_by_name(app, route_name: str):
    routes_to_remove = [route for route in app.routes if route.name == route_name]
    for route in routes_to_remove:
        app.routes.remove(route)