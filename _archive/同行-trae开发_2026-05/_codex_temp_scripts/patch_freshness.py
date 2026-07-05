#!/usr/bin/env python3
"""Patch learning pool freshness window from 7 to 14 days."""

from pathlib import Path

SCRIPT = Path("/Users/apple/Documents/同行资本内容部门/内容生产系统/09_runbooks/scripts/market_learning_pool_board_builder.py")

text = SCRIPT.read_text(encoding="utf-8")
original = text

text = text.replace("freshness_days: int = 7,", "freshness_days: int = 14,")

if text != original:
    SCRIPT.write_text(text, encoding="utf-8")
    print(f"Patched {SCRIPT}: freshness_days 7 -> 14")
else:
    print("No changes needed")
