from pathlib import Path
import logging

from smib.common.config import ROOT_DIRECTORY


class ModuleNameInjector(logging.Filter):
    def filter(self, record):

        record.module_name = ''
        if not Path(record.pathname).is_relative_to(ROOT_DIRECTORY.parent):
            record.module_name = Path(record.pathname).as_posix()
            return True

        relative_path = Path(record.pathname).relative_to(ROOT_DIRECTORY.parent).with_suffix('').as_posix().replace('/', '.')
        if 'Lib.site-packages.' in relative_path:
            relative_path = relative_path.split('Lib.site-packages.', 1)[1]

        record.module_name = relative_path

        return True
