import importlib.util
import logging
from pathlib import Path

from smib.config import PLUGINS_DIRECTORY


def load_plugins(directory: Path = PLUGINS_DIRECTORY):
    logger = logging.getLogger(load_plugins.__name__)
    logger.info(f'Plugin directory resolved to {directory.resolve()}')

    # Plugins are python packages defined in the plugins directory
    for python_package in directory.glob('*/__init__.py'):
        plugin = python_package.parent.relative_to(directory)
        logger.info(f"Found potential plugin: {plugin}")

        spec = importlib.util.spec_from_file_location(str(plugin), python_package)
        module = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            logger.exception(f"Failed to load plugin {plugin}: {repr(e)}", exc_info=True)
            continue

        if not hasattr(module, 'register') or not callable(getattr(module, 'register')):
            logger.info(f"{plugin} has no register function, skipping.")
            continue