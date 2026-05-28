#!/usr/bin/env python3
from __future__ import annotations

def build_evidence_map(ticker="300308.SZ"):
    claims = [
        {"claim":"product_mix_improving","claim_readable":"高端产品结构有改善迹象","supporting_evidence_count":2,"evidence_strength":"medium","source_types":["investor_relations_record","company_disclosure"],"limitations":["仍需财报验证收入质量和毛利率"]},
        {"claim":"order_visibility_improving","claim_readable":"订单能见度较好","supporting_evidence_count":2,"evidence_strength":"medium","source_types":["investor_relations_record"],"limitations":["客户订单具体数据未公开"]},
        {"claim":"shipment_signal_positive","claim_readable":"出货节奏正面","supporting_evidence_count":1,"evidence_strength":"medium","source_types":["quarterly_report"],"limitations":["需持续验证出货增长趋势"]},
        {"claim":"margin_signal_needs_validation","claim_readable":"毛利率信号需要验证","supporting_evidence_count":1,"evidence_strength":"low","source_types":["earnings_preview"],"limitations":["业绩预告提供方向但需要正式财报确认"]},
        {"claim":"customer_allocation_unconfirmed","claim_readable":"客户分配仍未确认","supporting_evidence_count":0,"evidence_strength":"unconfirmed","source_types":[],"limitations":["现有材料只能作为间接信号"]},
        {"claim":"supplier_share_unconfirmed","claim_readable":"供应商份额未确认","supporting_evidence_count":0,"evidence_strength":"unconfirmed","source_types":[],"limitations":["无直接证据"]},
        {"claim":"official_consensus_missing","claim_readable":"缺少权威一致预期","supporting_evidence_count":0,"evidence_strength":"unconfirmed","source_types":[],"limitations":["无法基准化预期差"]},
        {"claim":"valuation_gap_unconfirmed","claim_readable":"估值差未确认","supporting_evidence_count":0,"evidence_strength":"unconfirmed","source_types":[],"limitations":["估值边界仍为情景分析"]},
        {"claim":"bear_case_partially_mitigated","claim_readable":"空头风险部分缓解","supporting_evidence_count":1,"evidence_strength":"low","source_types":["industry_data"],"limitations":["竞争和定价风险仍存在"]}
    ]
    supported = sum(1 for c in claims if c["evidence_strength"] != "unconfirmed")
    return {"ticker": ticker, "evidence_to_claim_map": {"claims_checked": len(claims),
        "claims_supported": supported, "claims_unconfirmed": len(claims) - supported, "rows": claims}}
