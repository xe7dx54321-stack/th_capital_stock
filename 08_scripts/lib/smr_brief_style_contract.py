#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

RULES_PATH = Path(__file__).resolve().parents[2] / "config" / "brief_style_rules.json"

def load_rules():
    if RULES_PATH.exists():
        return json.loads(RULES_PATH.read_text(encoding="utf-8"))
    return _default_rules()

def _default_rules():
    return {"brief_type":"internal_watchlist_tracking_brief","style_name":"clear_internal_research_tracking_brief","target_reader":["boss","researcher"],"forbidden_styles":["sell_side_research_report","public_marketing_article","investment_recommendation"],"required_sections":["executive_brief","analyst_detail","why_not_pending","next_actions"],"writing_rules":{"start_with_conclusion":True,"max_bullets_per_section":5,"avoid_ai_tone":True,"avoid_sell_side_phrases":True}}

def build_contract():
    rules = load_rules()
    return {"brief_style_contract": rules, "note": "This is NOT a sell-side research report. It is an internal watchlist tracking brief."}
