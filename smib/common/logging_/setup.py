import json
import logging
import logging.config
from pathlib import Path

from smib.common.config import EXTERNAL_CONFIG_LOCATION
from smib.common.utils import get_module_name
from injectable import injectable_factory, load_injection_container, inject


def read_logging_json(path=EXTERNAL_CONFIG_LOCATION / 'logging.json'):
    path = Path(path)

    logging.basicConfig()
    logging.info(f'Resolving logging.json to {path}')

    if not (path.exists() and path.is_file()):
        logging.warning(f'No logging json file found at {path}')
        return None

    with open(path, 'rt') as file:
        config_file = json.load(file)
        return config_file


def setup_logging(path=EXTERNAL_CONFIG_LOCATION / 'logging.json'):
    try:
        logging.config.dictConfig(read_logging_json(path))
    except Exception as e:
        logging.basicConfig()
        logger = logging.getLogger('setup_logging')
        logger.warning(e)


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
