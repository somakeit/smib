import inspect
import json
import logging

from smib.common.config import ROOT_DIRECTORY
from smib.common.utils import get_module_name
from injectable import injectable_factory, load_injection_container, inject


def read_logging_json(path=ROOT_DIRECTORY / 'logging.json'):
    with open(path, 'rt') as file:
        config_file = json.load(file)
        return config_file


def setup_logging(path=ROOT_DIRECTORY / 'logging.json'):
    logging.config.dictConfig(read_logging_json(path))


@injectable_factory(logging.Logger, qualifier="plugin_logger")
def plugin_logger_factory():
    return logging.getLogger(get_module_name(2))


@injectable_factory(logging.Logger, qualifier="logger")
def logger_factory():
    return logging.getLogger(get_module_name(4))


if __name__ == '__main__':
    load_injection_container()
    setup_logging()
    logger: logging.Logger = inject("logger")

    logger.debug("debug message")
