from slack_bolt.app import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from smib.common.config import SLACK_APP_TOKEN, SLACK_BOT_TOKEN
from smib.slack import websocket_server
from smib.slack.error import handle_errors
from injectable import Autowired, load_injection_container, autowired, injectable_factory
from pprint import pprint


@injectable_factory(App, singleton=True, qualifier="SlackApp")
def create_slack_bolt_app():
    app = App(token=SLACK_BOT_TOKEN,
              raise_error_for_unhandled_request=True,
              request_verification_enabled=False,
              token_verification_enabled=False)
    app.error(handle_errors)

    @app.event("http_get_lights")
    def get_lights(event):
        pprint(event)

    return app


@autowired
def create_slack_socket_mode_handler(app: Autowired(App)):
    return SocketModeHandler(app,
                             app_token=SLACK_APP_TOKEN,
                             trace_enabled=True,
                             ping_pong_trace_enabled=True
                             )


def main():
    load_injection_container()
    slack_socket_mode_handler = create_slack_socket_mode_handler()

    websocket_server.start_threaded_server()
    slack_socket_mode_handler.start()


if __name__ == '__main__':
    main()
