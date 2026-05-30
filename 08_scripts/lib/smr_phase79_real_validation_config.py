#!/usr/bin/env python3
import json
from pathlib import Path
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "phase79_high_value_report_real_validation.json"
def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f:
        return json.load(f)
def validate_config(cfg=None):
    if cfg is None: cfg = load_config()
    checks = {}
    checks["strategy_is_real_validation"] = "real_network_validation" in cfg.get("strategy","")
    rv = cfg.get("real_network_validation", {})
    checks["real_network_enabled"] = rv.get("enabled", False) is True
    checks["save_raw_pdf_false"] = rv.get("save_raw_pdf", True) is False
    checks["save_raw_html_false"] = rv.get("save_raw_html", True) is False
    checks["ocr_false"] = rv.get("ocr_allowed", True) is False
    checks["browser_false"] = rv.get("browser_automation_allowed", True) is False
    qe = cfg.get("quantitative_extraction", {})
    checks["quant_enabled"] = qe.get("enabled", False) is True
    safety = cfg.get("safety", {})
    checks["mock_false"] = safety.get("mock_allowed", True) is False
    checks["fixture_false"] = safety.get("fixture_allowed", True) is False
    checks["pending_false"] = safety.get("pending_allowed", True) is False
    all_pass = all(checks.values())
    return {"all_pass": all_pass, "checks": checks}
