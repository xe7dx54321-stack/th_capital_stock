#!/usr/bin/env python3
"""Lightweight run logging for SMR scripts."""

import json
from datetime import datetime

from smr_paths import project_path

LOG_DIR = project_path("10_logs")
RUN_LOG_PATH = LOG_DIR / "script_runs.jsonl"


def log_run(script_name, status, message="", metrics=None):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "script": script_name,
        "status": status,
        "message": message,
        "metrics": metrics or {},
    }
    with open(RUN_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
