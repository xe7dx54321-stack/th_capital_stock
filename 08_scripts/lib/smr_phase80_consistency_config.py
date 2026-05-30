#!/usr/bin/env python3
import json
from pathlib import Path
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "phase80_report_quant_consistency_rules.json"
def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f: return json.load(f)
def validate_config(cfg=None):
    if cfg is None: cfg = load_config()
    checks = {"strategy_ok": "consistency" in cfg.get("strategy",""), "target_ok": cfg.get("target_ticker","")=="688041.SH", "revenue_covered": "revenue" in cfg.get("metrics",{}), "gm_covered": "gross_margin" in cfg.get("metrics",{}), "rd_covered": "R&D_expense" in cfg.get("metrics",{}), "ocf_covered": "operating_cash_flow" in cfg.get("metrics",{})}
    s=cfg.get("safety",{})
    checks.update({"mock_ok":not s.get("mock_allowed",True),"fixture_ok":not s.get("fixture_allowed",True),"raw_ok":not s.get("raw_save_allowed",True)})
    return {"all_pass":all(checks.values()),"checks":checks}
