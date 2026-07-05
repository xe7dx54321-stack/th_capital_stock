#!/usr/bin/env python3
"""Run learning pool refresh for today (2026-04-09)."""

import subprocess
import sys

SCRIPTS_DIR = "/Users/apple/Documents/同行资本内容部门/内容生产系统/09_runbooks/scripts"

# Step 1: Run memo builder
print("=== Step 1: Learning Memo Builder ===")
result = subprocess.run(
    [sys.executable, f"{SCRIPTS_DIR}/market_learning_memo_builder.py",
     "--date", "2026-04-09", "--count", "8", "--write-log"],
    capture_output=True, text=True, timeout=120,
)
print(f"Exit: {result.returncode}")
if result.stdout:
    print(result.stdout[-1000:])
if result.stderr:
    print(f"STDERR: {result.stderr[-500:]}")

# Step 2: Run pool board builder
print("\n=== Step 2: Learning Pool Board Builder ===")
result = subprocess.run(
    [sys.executable, f"{SCRIPTS_DIR}/market_learning_pool_board_builder.py",
     "--date", "2026-04-09", "--count", "8", "--write", "--write-log"],
    capture_output=True, text=True, timeout=180,
)
print(f"Exit: {result.returncode}")
if result.stdout:
    print(result.stdout[-1000:])
if result.stderr:
    print(f"STDERR: {result.stderr[-500:]}")

print("\n=== Done ===")
