__display_name__ = "API & Database Docs"
__description__ = "Plugin to override the default API docs, allowing for customisation, and database schema documentation."
__author__ = "Sam Cork"

from smib.db.manager import DatabaseManager
from smib.events.interfaces.http.http_web_event_interface import WebEventInterface

FAVICON_URL = "https://raw.githubusercontent.com/somakeit/graphics/refs/heads/master/favicon.png"
LOGO_URL = "https://raw.githubusercontent.com/somakeit/graphics/refs/heads/master/logo-padded-256.png"

def register(web: WebEventInterface, database: DatabaseManager):
    from .api_docs import register as register_api_docs
    from .db_docs import register as register_db_docs

    register_api_docs(web)
    register_db_docs(database, web)