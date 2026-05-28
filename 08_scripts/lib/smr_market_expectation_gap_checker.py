#!/usr/bin/env python3
from __future__ import annotations
from typing import Any

def check_market_gap():
    return {"market_current_belief": ["AI光模块需求强","800G放量仍在持续","头部光模块公司处于景气周期"],
        "our_variant_view": ["市场可能已经反映行业高景气，但未必充分反映高端产品结构和毛利率稳定性的组合影响"],
        "expectation_gap_status": "potential_but_unconfirmed",
        "expectation_gap_confidence": "medium_low",
        "consensus_source_status": "not_authoritatively_confirmed",
        "what_would_confirm_gap": ["季报收入高增且毛利率稳定","1.6T出货节奏明确","一致预期尚未明显上修"],
        "what_would_disprove_gap": ["收入兑现但毛利率明显下滑","市场一致预期已充分上修","客户需求或资本开支放缓"]}

def build_gap_report(ticker="300308.SZ"):
    return {"ticker": ticker, "market_expectation_gap": check_market_gap()}
