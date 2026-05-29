#!/usr/bin/env python3
"""Deep evidence claim mapper - Phase 66."""
from typing import Any

CLAIM_DEFINITIONS={
    "800G_signal_supported":{"variable":"800G_product_signal","threshold":1,"strength_input":["management_commentary","financial_report_context","business_context"]},
    "1_6T_signal_supported":{"variable":"1_6T_product_signal","threshold":1,"strength_input":["management_commentary","financial_report_context"]},
    "product_mix_partially_supported":{"variable":"high_end_product_mix","threshold":1,"strength_input":["management_commentary","financial_report_context"]},
    "shipment_delivery_supported":{"variable":"shipment_delivery_signal","threshold":1,"strength_input":["management_commentary","business_context"]},
    "customer_demand_proxy_supported":{"variable":"customer_demand_signal","threshold":1,"strength_input":["management_commentary","business_context"]},
    "order_visibility_partially_supported":{"variable":"order_visibility_signal","threshold":1,"strength_input":["management_commentary","proxy_signal"]},
    "asp_trend_unconfirmed":{"variable":"asp_price_signal","threshold":5,"strength_input":["strong_direct_disclosure"]},
    "customer_share_unconfirmed":{"variable":"customer_demand_signal","threshold":5,"strength_input":["strong_direct_disclosure"]},
    "specific_order_volume_unconfirmed":{"variable":"order_visibility_signal","threshold":5,"strength_input":["strong_direct_disclosure"]},
    "capacity_expansion_supported":{"variable":"capacity_expansion_signal","threshold":1,"strength_input":["management_commentary","financial_report_context","business_context"]},
    "risk_or_contradictory_signal_present":{"variable":"*","threshold":1,"strength_input":["risk_or_contradictory_signal"]},
}

def map_evidence_to_claims(evidence_rows:list[dict])->dict[str,Any]:
    claims_checked=0;claims_supported=0;claims_partially_supported=0;claims_unconfirmed=0
    risk_count=0;claim_results=[]
    for claim_name,defn in CLAIM_DEFINITIONS.items():
        claims_checked+=1
        supporting=[ev for ev in evidence_rows if (defn["variable"]=="*" or ev.get("business_variable")==defn["variable"]) and ev.get("evidence_strength","") in defn["strength_input"]]
        count=len(supporting)
        new_count=count
        if claim_name.endswith("_unconfirmed"):
            claims_unconfirmed+=1
            claim_results.append({"claim":claim_name,"claim_status":"unconfirmed","supporting_evidence_count":0,"new_evidence_count":0,"evidence_strength_mix":{},"limitation":"该变量需要strong_direct_disclosure证据级别，当前信息披露不满足。"})
            continue
        if claim_name=="risk_or_contradictory_signal_present":
            if count>0:
                risk_count+=1
                claim_results.append({"claim":claim_name,"claim_status":"risk_signal_found","supporting_evidence_count":count,"new_evidence_count":count,"evidence_strength_mix":{"risk_or_contradictory_signal":count},"limitation":"存在反向或风险信号，需要进一步研究。"})
            else:
                claim_results.append({"claim":claim_name,"claim_status":"no_risk_signal","supporting_evidence_count":0,"new_evidence_count":0,"evidence_strength_mix":{},"limitation":"当前未发现明确的反向或风险信号。"})
            continue
        if count>=defn["threshold"]:
            claims_supported+=1
            strength_mix={}
            for ev in supporting:
                s=ev.get("evidence_strength","")
                strength_mix[s]=strength_mix.get(s,0)+1
            claim_results.append({"claim":claim_name,"claim_status":"supported","supporting_evidence_count":count,"new_evidence_count":new_count,"evidence_strength_mix":strength_mix,"limitation":"支持相关方向，但仍不能确认具体数量指标。"})
        else:
            claims_partially_supported+=1
            claim_results.append({"claim":claim_name,"claim_status":"partially_supported","supporting_evidence_count":count,"new_evidence_count":new_count,"evidence_strength_mix":{},"limitation":"证据不足，需要更多真实披露文本支持此判断。"})
    evidence_gain=claims_supported
    return {"claims_checked":claims_checked,"claims_supported":claims_supported,"claims_partially_supported":claims_partially_supported,"claims_unconfirmed":claims_unconfirmed,"claims_with_risk_signal":risk_count,"evidence_gain_delta":evidence_gain,"rows":claim_results}
