import logging
from datetime import datetime, UTC

class UTCFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=UTC)
        return dt.isoformat()
