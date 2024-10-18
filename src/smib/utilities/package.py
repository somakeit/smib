from pathlib import Path

def get_package_root() -> Path:
    """ Returns the smib package root directory """
    import smib
    return Path(smib.__file__).parent