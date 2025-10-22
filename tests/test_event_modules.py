import importlib
import types
import pytest

@pytest.mark.parametrize(
    "name",
    [
        "smib.events",
        "smib.events.handlers",
        "smib.events.handlers.http_event_handler",
        "smib.events.handlers.slack_event_handler",
        "smib.events.handlers.scheduled_event_handler",
        "smib.events.services",
        "smib.events.services.http_event_service",
        "smib.events.services.slack_event_service",
        "smib.events.services.scheduled_event_service",
        "smib.events.requests",
        "smib.events.requests.copyable_starlette_request",
        "smib.events.responses",
        "smib.events.responses.http_bolt_response",
        "smib.events.interfaces",
        "smib.events.interfaces.http",  # Changed: this is a package, not a module
        "smib.events.interfaces.http.http_api_event_interface",  # Added
        "smib.events.interfaces.http.http_web_event_interface",  # Added
        "smib.events.interfaces.slack_event_interface",
        "smib.events.interfaces.scheduled_event_interface",
        "smib.events.middlewares",
        "smib.events.middlewares.http_middleware",
    ],
)
def test_event_layer_imports(name: str):
    mod = importlib.import_module(name)
    assert isinstance(mod, types.ModuleType)
