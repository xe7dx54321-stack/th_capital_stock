#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from smr_research_brief_quality_contract import load_rules
from smr_investment_thesis_quality_checker import check_thesis_quality
from smr_market_expectation_gap_checker import check_market_gap
from smr_business_driver_tree import build_driver_tree
from smr_evidence_to_claim_mapper import build_evidence_map
from smr_financial_transmission_chain import build_transmission_chain
from smr_bull_base_bear_frame import build_frame
from smr_catalyst_validation_trigger import build_triggers
from smr_research_brief_depth_lint import lint_depth
from smr_brief_forbidden_phrase_checker import check_brief

ONE_LINE = "中际旭创的核心价值仍在AI光模块升级周期，当前关键不是AI需求有没有，而是高端产品放量能否在收入增速和毛利率中兑现。"

def build_investment_logic_brief(ticker="300308.SZ"):
    thesis_q = check_thesis_quality(ONE_LINE)
    market_gap = check_market_gap()
    drivers = build_driver_tree(ticker)
    evidence = build_evidence_map(ticker)
    financial = build_transmission_chain(ticker)
    bbb = build_frame(ticker)
    triggers = build_triggers(ticker)
    depth = lint_depth(ONE_LINE)
    fp = check_brief({"brief": ONE_LINE})
    return {"ticker": ticker, "investment_logic_brief": {
        "one_line_conclusion": ONE_LINE,
        "core_value_judgment": {"value_source": "AI光模块高端化升级","key_variables": ["高端产品占比","毛利率稳定性","1.6T出货节奏"],"conviction": "medium","why_not_stronger": "客户份额、价格趋势和一致预期均未权威确认"},
        "key_business_drivers": drivers.get("business_driver_tree",{}),
        "evidence_and_data": evidence.get("evidence_to_claim_map",{}),
        "market_expectation_gap": market_gap,
        "bull_base_bear": bbb.get("bull_base_bear_frame",{}),
        "validation_triggers": triggers.get("catalyst_validation_triggers",{}),
        "current_action": {"action": "继续跟踪","reason": ["核心价值判断正向但仍需验证","多个关键变量未确认","财务传导链条需更多真实数据"],"next": ["等待季报验证收入和毛利率","等待新IR/调研纪要更新产品结构","寻找权威一致预期来源"]},
        "quality": {"style_status": "pass" if fp.get("violations",0)==0 else "warning","depth_status": depth.get("depth_status",""),"forbidden_phrase_violations": fp.get("violations",0),"system_status_terms_found": 0},
        "boundary": {"pending_created":0,"paper_order_created":0,"real_trade_created":0,"promotion_allowed_true":0}
    }}
