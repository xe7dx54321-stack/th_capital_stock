#!/usr/bin/env python3
"""Safely deploy the current harvester file without embedding stale source code."""

import shutil
from pathlib import Path

ROOT = Path("/Users/apple/Documents/同行资本二级市场")
SOURCE = ROOT / "08_scripts/data_harvester/ah_daily_bar.py"
TARGET = ROOT / "08_scripts/data_harvester/ah_daily_bar.py"


def main():
    if not SOURCE.exists():
        raise SystemExit(f"Missing source harvester: {SOURCE}")

    TARGET.parent.mkdir(parents=True, exist_ok=True)

    if SOURCE.resolve() == TARGET.resolve():
        print(f"No-op deploy: source and target are the same file: {SOURCE}")
        return

    shutil.copy2(SOURCE, TARGET)
    print(f"Deployed current harvester from {SOURCE} -> {TARGET}")


if __name__ == "__main__":
    main()
