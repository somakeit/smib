from pathlib import Path


def is_running_in_docker() -> bool:
    path = Path('/.dockerenv')
    return path.exists()