from enum import StrEnum


class BoltEventType(StrEnum):
    HTTP = 'http'
    SCHEDULED = 'scheduled'
    WEBSOCKET = 'websocket'