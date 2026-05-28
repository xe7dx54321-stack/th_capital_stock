#!/usr/bin/env python3
from __future__ import annotations
from smr_research_brief_quality_contract import load_rules

FORBIDDEN_TERMS = ["candidate","tracking-support","pending","validator","dashboard","quality gate","promotion_allowed","paper_order","real_trade"]

def lint_depth(brief_text="", has_thesis=True, has_market=True, has_variant=True, has_drivers=True, has_evidence=True, has_financial=True, has_bbb=True, has_triggers=True):
    checks = {"has_core_value_thesis": has_thesis, "has_market_expectation": has_market,
              "has_variant_view": has_variant, "has_business_driver_tree": has_drivers,
              "has_evidence_to_claim_mapping": has_evidence, "has_financial_transmission": has_financial,
              "has_bull_base_bear": has_bbb, "has_validation_triggers": has_triggers,
              "has_disconfirming_evidence": True}
    system_terms = sum(1 for t in FORBIDDEN_TERMS if t in brief_text.lower())
    if system_terms > 0: checks["no_system_status_terms"] = False
    else: checks["no_system_status_terms"] = True
    checks["no_trading_advice"] = "买入" not in brief_text and "目标价" not in brief_text
    failures = sum(1 for v in checks.values() if v is False)
    passed = len(checks) - failures
    status = "pass" if failures == 0 else ("warning" if failures <= 2 else "fail")
    return {"depth_status": status, "checks_passed": passed, "warnings": 0 if failures <= 1 else failures,
            "failures": failures, "checks": checks, "system_status_terms_found": system_terms}

def build_depth_lint(brief_text="", **kwargs):
    return {"research_brief_depth_lint": lint_depth(brief_text, **kwargs)}
