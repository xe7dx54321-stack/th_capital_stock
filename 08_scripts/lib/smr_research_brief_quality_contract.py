#!/usr/bin/env python3
from __future__ import annotations
import json; from pathlib import Path
RULES_PATH = Path(__file__).resolve().parents[2] / "config" / "research_brief_quality_rules.json"
def load_rules():
    if RULES_PATH.exists(): return json.loads(RULES_PATH.read_text(encoding="utf-8"))
    return {"brief_type":"internal_equity_research_logic_brief","required_business_questions":["core_value_thesis","market_expectation","key_business_drivers"]}
def build_contract():
    rules = load_rules()
    return {"research_brief_quality_contract": rules, "note": "NOT system status report. Must answer business value questions."}
