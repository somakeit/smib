from enum import StrEnum

from slack_sdk.signature import Clock, SignatureVerifier

from smib.config import slack


class BoltRequestMode(StrEnum):
    SOCKET_MODE = 'socket_mode'
    HTTP = 'http_request'
    SCHEDULED = 'scheduled'

def get_slack_signature_headers(body: str | bytes) -> dict[str, str]:
    verifier = SignatureVerifier(slack.signing_secret.get_secret_value())
    timestamp = str(int(verifier.clock.now()))
    headers = {
        "x-slack-request-timestamp": timestamp,
        "x-slack-signature": verifier.generate_signature(timestamp=timestamp, body=body)
    }
    return headers