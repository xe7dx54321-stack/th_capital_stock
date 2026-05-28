#!/usr/bin/env python3
from __future__ import annotations

def build_triggers(ticker="300308.SZ"):
    return {"ticker": ticker, "catalyst_validation_triggers": {
        "strengthening_triggers": [
            {"event":"季报收入高增且毛利率稳定","why_it_matters":"验证高端产品放量是否带来利润弹性","expected_action":"upgrade_research_conviction"},
            {"event":"新IR明确1.6T出货节奏","why_it_matters":"验证下一代产品放量节奏","expected_action":"refresh_thesis"},
            {"event":"权威一致预期来源确认","why_it_matters":"可基准化预期差","expected_action":"recalibrate_expectation_gap"}
        ],
        "weakening_triggers": [
            {"event":"收入增长但毛利率明显下滑","why_it_matters":"价格压力可能抵消产品结构升级","expected_action":"downgrade_research_conviction"},
            {"event":"大客户资本开支放缓","why_it_matters":"削弱订单能见度","expected_action":"reassess_demand_assumption"},
            {"event":"竞争加剧/新进入者","why_it_matters":"可能影响份额和定价","expected_action":"reassess_competitive_position"}
        ],
        "forbidden_actions": ["create_order","create_trade","issue_buy_signal","issue_sell_signal"]
    }}
