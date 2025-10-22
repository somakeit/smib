# Ensures "src" is on sys.path so `import smib` and `import plugins` work
# even when running `pytest` from the repo root without special PYTHONPATH.
import sys
from pathlib import Path

def _add_src_to_syspath() -> None:
    project_root = Path(__file__).resolve().parents[1]
    src_path = project_root / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))

_add_src_to_syspath()
