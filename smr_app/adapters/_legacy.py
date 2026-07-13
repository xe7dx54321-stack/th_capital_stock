from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEGACY_LIB_DIR = PROJECT_ROOT / "08_scripts" / "lib"


def import_domain_module(name: str) -> ModuleType:
    if str(LEGACY_LIB_DIR) not in sys.path:
        sys.path.insert(0, str(LEGACY_LIB_DIR))
    return importlib.import_module(name)
