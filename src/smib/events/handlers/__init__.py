from enum import StrEnum


class BoltRequestMode(StrEnum):
    SOCKET_MODE = 'socket_mode'
    HTTP = 'http_request'
    SCHEDULED = 'scheduled'