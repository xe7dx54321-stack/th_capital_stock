#!/usr/bin/env python3
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "phase76_pdf_recovery_known_url_breakthrough.json"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_config(cfg=None):
    if cfg is None:
        cfg = load_config()
    checks = {}
    checks["strategy_is_pdf_recovery"] = cfg.get("strategy") == "pdf_recovery_and_known_url_breakthrough"
    safety = cfg.get("safety", {})
    checks["mock_allowed"] = safety.get("mock_allowed", True) is False
    checks["fixture_allowed"] = safety.get("fixture_allowed", True) is False
    checks["pdf_recovery_enabled"] = cfg.get("pdf_recovery", {}).get("enabled", False) is True
    checks["known_url_enabled"] = cfg.get("known_url_breakthrough", {}).get("enabled", False) is True
    checks["save_raw_pdf"] = cfg.get("pdf_recovery", {}).get("save_raw_pdf", True) is False
    checks["ocr_allowed"] = cfg.get("pdf_recovery", {}).get("ocr_allowed", True) is False
    all_pass = all(checks.values())
    return {"all_pass": all_pass, "checks": checks}
