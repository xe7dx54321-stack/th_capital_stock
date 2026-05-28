#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from smr_brief_style_contract import load_rules
from smr_brief_forbidden_phrase_checker import check_brief

def lint_brief(brief_text, has_conclusion=True, has_exec=True, has_detail=True, has_next=True, has_why_not=True):
    # Positive checks (True = good)
    positive = {"has_conclusion_first": has_conclusion, "has_executive_brief": has_exec,
                "has_analyst_detail": has_detail, "has_next_actions": has_next,
                "has_why_not_pending": has_why_not, "field_dump_detected": len(brief_text) < 2000}
    # Negative checks (False = good)
    trading_advice = "买入" in brief_text or "卖出" in brief_text or ("buy" in brief_text.lower() and "signal" not in brief_text.lower())
    target_price = "目标价" in brief_text or "target price" in brief_text.lower()
    position = "仓位" in brief_text
    negative = {"trading_advice_detected": trading_advice,
                "target_price_detected": target_price,
                "position_sizing_detected": position}

    all_checks = {**positive, **negative}
    failures = sum(1 for v in positive.values() if v is False) + sum(1 for v in negative.values() if v is True)
    warnings = 1 if len(brief_text) > 3000 else 0
    passed = len(all_checks) - failures
    status = "pass" if failures == 0 and warnings == 0 else ("warning" if failures == 0 else "fail")
    return {"style_status": status, "checks_passed": passed, "warnings": warnings,
            "failures": failures, "checks": all_checks}

def build_lint(brief_text, has_conclusion=True, has_exec=True, has_detail=True, has_next=True, has_why_not=True):
    return {"brief_style_lint": lint_brief(brief_text, has_conclusion, has_exec, has_detail, has_next, has_why_not)}
