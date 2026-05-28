#!/usr/bin/env python3
from __future__ import annotations

def build_transmission_chain(ticker="300308.SZ"):
    chains = [
        {"business_driver":"高端产品占比提升","financial_metric":"收入质量/ASP","current_evidence_status":"partially_supported","what_to_verify":"高端产品放量是否带来收入增长且毛利率稳定"},
        {"business_driver":"订单能见度","financial_metric":"收入确定性","current_evidence_status":"partially_supported","what_to_verify":"订单能见度能否转化为实际收入确认"},
        {"business_driver":"出货节奏","financial_metric":"当期收入确认","current_evidence_status":"partially_supported","what_to_verify":"出货节奏是否持续"},
        {"business_driver":"价格趋势","financial_metric":"毛利率","current_evidence_status":"insufficient","what_to_verify":"价格压力是否抵消产品结构升级"},
        {"business_driver":"毛利率稳定性","financial_metric":"利润弹性","current_evidence_status":"insufficient","what_to_verify":"毛利率能否保持稳定"},
        {"business_driver":"一致预期","financial_metric":"估值/预期差判断","current_evidence_status":"unconfirmed","what_to_verify":"需要权威一致预期来量化预期差"}
    ]
    return {"ticker": ticker, "financial_transmission_chain": {"chains": chains, "overall_status": "financial_transmission_partially_supported"}}
