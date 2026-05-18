#!/usr/bin/env python3
"""Legacy deploy helper retired - validates current maintained scripts instead of overwriting them."""

import py_compile
from pathlib import Path

ROOT = Path("/Users/apple/Documents/同行资本二级市场")
SCRIPT_PATHS = [
    ROOT / "08_scripts/factor_engine/trend.py",
    ROOT / "08_scripts/factor_engine/fundamental.py",
    ROOT / "08_scripts/factor_engine/us_linkage.py",
    ROOT / "08_scripts/risk_engine/monitor.py",
]


def main():
    missing = [str(path) for path in SCRIPT_PATHS if not path.exists()]
    if missing:
        raise SystemExit("Missing maintained scripts:\n" + "\n".join(missing))

    for path in SCRIPT_PATHS:
        py_compile.compile(str(path), doraise=True)
        print(f"Validated current script: {path}")

    print("Legacy deploy_scripts.py is now safe: it validates maintained scripts and performs no overwrite.")


if __name__ == "__main__":
    main()
