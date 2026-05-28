#!/usr/bin/env python3
from __future__ import annotations
from typing import Any

THESIS_PATTERNS = {"core_value_source":["价值","驱动","业务","收入","利润","毛利率","产品结构","份额","升级","迭代","放量","需求","增长"],
    "weak_only_tracking":["继续跟踪","维持跟踪","保持关注","暂时观望","暂不操作"]}

def check_thesis_quality(thesis_text=""):
    text = thesis_text or ""
    has_value = any(kw in text for kw in THESIS_PATTERNS["core_value_source"])
    is_weak = any(kw in text for kw in THESIS_PATTERNS["weak_only_tracking"]) and len(text) < 50
    has_company = any(c in text for c in ["中际","旭创","公司","光模块","800G","1.6T","高端产品"])
    has_profit_driver = any(p in text for p in ["毛利率","利润","收入","ASP"])
    checks = {"has_core_value_thesis": has_value, "has_company_specific_logic": has_company,
              "has_profit_driver": has_profit_driver, "not_only_tracking_status": not is_weak,
              "has_uncertainty": "仍需" in text or "未确认" in text or "待验证" in text}
    failures = sum(1 for v in checks.values() if v is False)
    status = "pass" if failures <= 1 else ("warning" if failures <= 2 else "fail")
    return {"overall_status": status, "core_value_thesis": text[:200] if text else "N/A",
            "business_value_source": ["高端产品占比提升","AI客户需求持续性","毛利率稳定性"],
            "checks": checks}

def build_report(thesis_text="", ticker="300308.SZ"):
    return {"ticker": ticker, "investment_thesis_quality": check_thesis_quality(thesis_text)}
