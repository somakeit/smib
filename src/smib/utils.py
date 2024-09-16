from pathlib import Path
import smib


def get_root_path():
    return Path(smib.__file__).resolve().parent.parent
