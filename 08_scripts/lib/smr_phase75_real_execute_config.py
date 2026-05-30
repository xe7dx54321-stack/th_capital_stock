#!/usr/bin/env python3
# Phase 75: Real execute config loader
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "phase75_fallback_html_real_execute.json"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_config(cfg=None):
    if cfg is None:
        cfg = load_config()
    checks = {}
    checks["real_execute_required"] = cfg.get("real_execute_required", False) is True
    safety = cfg.get("safety", {})
    checks["save_raw_html"] = safety.get("save_raw_html", True) is False
    checks["ocr_allowed"] = safety.get("ocr_allowed", True) is False
    checks["mock_allowed"] = safety.get("mock_allowed", True) is False
    checks["fixture_allowed"] = safety.get("fixture_allowed", True) is False
    checks["pending_allowed"] = safety.get("pending_allowed", True) is False
    checks["paper_order_allowed"] = safety.get("paper_order_allowed", True) is False
    checks["real_trade_allowed"] = safety.get("real_trade_allowed", True) is False
    all_pass = all(checks.values())
    return {"all_pass": all_pass, "checks": checks}
