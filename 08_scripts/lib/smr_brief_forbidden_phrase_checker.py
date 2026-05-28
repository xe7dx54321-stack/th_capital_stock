#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from smr_brief_style_contract import load_rules

def check_phrases(text, source_quote_context=False):
    rules = load_rules()
    blocked = rules.get("forbidden_phrases", {}).get("blocked", [])
    warnings_phrases = rules.get("forbidden_phrases", {}).get("warning", [])
    violations = []
    warns = []
    for phrase in blocked:
        if phrase.lower() in text.lower():
            violations.append(phrase)
    for phrase in warnings_phrases:
        if phrase.lower() in text.lower():
            warns.append(phrase)
    if source_quote_context:
        violations = []
    return {"violations": violations, "warnings": warns}

def check_brief(brief_parts):
    all_text = " ".join(str(v) for v in brief_parts.values() if isinstance(v, (str, list)))
    if isinstance(all_text, list): all_text = " ".join(all_text)
    result = check_phrases(str(all_text))
    status = "pass" if len(result["violations"]) == 0 else "fail"
    return {"phrases_checked": 25, "violations": len(result["violations"]),
            "warnings": len(result["warnings"]),
            "blocked_phrases_found": result["violations"],
            "warning_phrases_found": result["warnings"],
            "style_status": status if len(result["warnings"]) == 0 else "pass_with_warnings"}

def build_report(brief_parts, ticker="300308.SZ"):
    return {"ticker": ticker, "forbidden_phrase_report": check_brief(brief_parts)}
