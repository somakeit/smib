import logging
from pathlib import Path

from logging.handlers import TimedRotatingFileHandler


class EnsureDirectoryTimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """
    Handler for logging to a file, rotating the log file at certain timed
    intervals.

    If backupCount is > 0, when rollover is done, no more than backupCount
    files are kept - the oldest ones are deleted.

    This handler ensures that the directory for log files exists. If the directory does not exist,
    it is created automatically before initializing the base handler.

    Usage:
    logger = logging.getLogger(__name__)
    handler = EnsureDirectoryTimedRotatingFileHandler('/path/to/logfile.log', when='midnight')
    logger.addHandler(handler)
    """

    def __init__(self, filename, when='h', interval=1, backupCount=0, encoding=None, delay=False, utc=False,
                 atTime=None, errors=None):
        """
        Initialize the handler.

        :param filename: The filename for log file.
        :type filename: str
        """
        directory = Path(filename).parent
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
        super().__init__(filename, when, interval, backupCount, encoding, delay, utc, atTime, errors)
