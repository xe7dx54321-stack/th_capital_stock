#!/usr/bin/env python3
"""Deep business evidence extractor - Phase 66."""
import hashlib
from typing import Any

BUSINESS_VARIABLES={
    "800G_product_signal":["800G","800 G"],
    "1_6T_product_signal":["1.6T","1.6 T"],
    "high_end_product_mix":["产品结构","高端产品","产品升级","高速光模块","硅光","CPO","LPO"],
    "shipment_delivery_signal":["出货","交付","量产","排产","供应链"],
    "customer_demand_signal":["客户需求","海外客户","AI客户","云厂商","大客户","数据中心"],
    "order_visibility_signal":["订单","在手订单","能见度","需求能见度","指引"],
    "asp_price_signal":["ASP","价格","单价","价格竞争","降价","毛利率","毛利水平"],
    "capacity_expansion_signal":["产能","扩产","产能利用率","泰国","墨西哥","越南"],
}

EVIDENCE_STRENGTHS=["strong_direct_disclosure","management_commentary","financial_report_context","business_context","proxy_signal","risk_or_contradictory_signal","review_required"]

def extract_deep_evidence(texts:list[dict])->dict[str,Any]:
    evidence_list=[];ev_id=0
    for t in texts:
        text=t.get("text","");sid=t.get("source_id","");src_type=t.get("source_type","")
        if not text or len(text)<100: continue
        for var_name,keywords in BUSINESS_VARIABLES.items():
            matched_kw=[kw for kw in keywords if kw.lower() in text.lower()]
            if not matched_kw: continue
            ev_id+=1
            pos=min((text.lower().find(kw.lower()) for kw in matched_kw if kw.lower() in text.lower()),default=0)
            start=max(0,pos-60);end=min(len(text),pos+200)
            span=text[start:end].replace("\n"," ").replace("\r"," ")[:240]
            span_hash=hashlib.sha256(span.encode("utf-8")).hexdigest()[:12]
            strength=_determine_strength(var_name,src_type,matched_kw)
            confidence=_determine_confidence(var_name,len(matched_kw))
            limitation=_generate_limitation(var_name)
            cannot_conclude=_generate_cannot_conclude(var_name)
            evidence_list.append({
                "evidence_id":f"phase66_biz_ev_{ev_id:03d}",
                "source_id":sid,"source_type":src_type,
                "business_variable":var_name,"claim_type":var_name+"_supported",
                "quoted_span":span,"span_location_hash":span_hash,
                "evidence_strength":strength,"confidence":confidence,
                "limitation":limitation,"cannot_conclude":cannot_conclude,
                "keywords_hit":matched_kw,"allowed_usage":"real_disclosure_evidence",
                "requires_human_review":strength=="review_required"
            })
    strengths_count={s:0 for s in EVIDENCE_STRENGTHS}
    for ev in evidence_list:
        s=ev.get("evidence_strength","")
        strengths_count[s]=strengths_count.get(s,0)+1
    return {"texts_scanned":len(texts),"evidence_created":len(evidence_list),"strong_direct_disclosure":strengths_count.get("strong_direct_disclosure",0),"management_commentary":strengths_count.get("management_commentary",0),"financial_report_context":strengths_count.get("financial_report_context",0),"business_context":strengths_count.get("business_context",0),"proxy_signal":strengths_count.get("proxy_signal",0),"risk_or_contradictory_signal":strengths_count.get("risk_or_contradictory_signal",0),"review_required":strengths_count.get("review_required",0),"rows":evidence_list}

def _determine_strength(var:str,src_type:str,matched_kw:list[str])->str:
    if var in ("asp_price_signal",): return "review_required"
    if src_type=="annual_report": return "financial_report_context"
    if src_type in ("investor_relations_record","performance_briefing_or_earnings_call"):
        return "management_commentary"
    if src_type in ("semiannual_report","quarterly_report"): return "financial_report_context"
    return "business_context"

def _determine_confidence(var:str,kw_count:int)->str:
    if kw_count>=4: return "medium"
    if kw_count>=2: return "low_medium"
    return "low"

def _generate_limitation(var:str)->str:
    limitations={
        "800G_product_signal":"真实披露文本提及800G相关产品，但不能确认800G收入占比、出货量或客户分配。",
        "1_6T_product_signal":"真实披露文本提及1.6T相关进展，但不能确认大规模放量时间、量产状态或收入贡献。",
        "high_end_product_mix":"真实披露文本提及产品结构相关信息，但不能确认具体产品级收入占比或毛利率。",
        "shipment_delivery_signal":"真实披露文本提及出货或交付相关表述，但不能确认具体出货量、客户或ASP。",
        "customer_demand_signal":"真实披露文本提及客户需求相关表述，但不能确认客户份额、具体客户关系或订单分配。",
        "order_visibility_signal":"真实披露文本提及订单或能见度，但不能确认具体订单金额、订单量或客户。",
        "asp_price_signal":"真实披露文本提及ASP或价格相关信息，必须谨慎解读，不能直接确认ASP趋势。",
        "capacity_expansion_signal":"真实披露文本提及产能或扩产相关信息，但不能确认产能释放节奏、订单匹配或投资回报。",
    }
    return limitations.get(var,"需要进一步人工审阅以确认证据强度。")

def _generate_cannot_conclude(var:str)->list[str]:
    cc={
        "800G_product_signal":["800G revenue share","specific customer allocation","exact shipment volume"],
        "1_6T_product_signal":["1.6T mass production timeline","1.6T revenue contribution","specific customer orders"],
        "high_end_product_mix":["product-level revenue share","product-level gross margin","specific product roadmap"],
        "shipment_delivery_signal":["exact shipment volume","exact delivery schedule","per-customer allocation"],
        "customer_demand_signal":["customer share","specific customer names","order allocation from specific customers"],
        "order_visibility_signal":["specific order amount","specific order volume","revenue projection"],
        "asp_price_signal":["ASP trend","exact ASP level","margin impact from ASP"],
        "capacity_expansion_signal":["capacity release schedule","order-to-capacity matching","capex ROI"],
    }
    return cc.get(var,["requires human review"])
