from pathlib import Path


def is_empty_directory(path: Path | str) -> bool:
    """Check if a directory is empty."""
    return not any(Path(path).iterdir())