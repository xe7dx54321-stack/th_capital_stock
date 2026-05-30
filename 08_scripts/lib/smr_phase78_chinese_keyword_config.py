#!/usr/bin/env python3
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "phase78_generic_hard_tech_chinese_keywords.json"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def validate_config(cfg=None):
    if cfg is None:
        cfg = load_config()
    checks = {}
    checks["strategy_is_chinese_keyword_repair"] = cfg.get("strategy") == "chinese_keyword_matching_repair"
    safety = cfg.get("safety", {})
    checks["keyword_hit_not_confirmed"] = safety.get("keyword_hit_not_confirmed", False) is True
    checks["context_required"] = safety.get("context_required", False) is True
    checks["legal_governance_exclusion"] = safety.get("legal_governance_exclusion_required", False) is True
    variables = cfg.get("variables", {})
    for var_name in variables:
        chinese = variables[var_name].get("chinese_keywords", [])
        checks[f"{var_name}_has_chinese"] = len(chinese) > 0
    all_pass = all(checks.values())
    return {"all_pass": all_pass, "checks": checks}
