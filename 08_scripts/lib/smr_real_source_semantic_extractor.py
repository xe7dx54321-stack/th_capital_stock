#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import generate_execution_id, now_ts

TRACKED_VARIABLES = ["product_mix","order_visibility","shipment","ASP_price_proxy","margin_signal","bear_case_evidence","valuation_boundary","customer_allocation_proxy","supplier_share_scenario","official_consensus_status"]
VAR_KEYWORDS = {"product_mix":["产品","高端","800G","光模块","占比"],"order_visibility":["订单","可见","需求","客户"],"shipment":["出货","交付","shipment"],"ASP_price_proxy":["价格","ASP","定价","毛利率"],"margin_signal":["毛利率","净利率","利润"],"bear_case_evidence":["风险","不确定","竞争","降价"],"valuation_boundary":["估值","PE","PS","EV"],"customer_allocation_proxy":["客户","供应商","供应链"],"supplier_share_scenario":["份额","供应商"],"official_consensus_status":["一致预期","consensus","预测"]}

def extract_semantic(chunk):
    text=chunk.get("content","") or ""; extractions=[]
    for var in TRACKED_VARIABLES:
        keywords=VAR_KEYWORDS.get(var,[])
        if any(kw in text for kw in keywords):
            span=text[:200]
            extractions.append({"extraction_id":generate_execution_id(f"extract_{chunk.get('chunk_id','')[:10]}_{var}"),"chunk_id":chunk.get("chunk_id"),"source_id":chunk.get("source_id"),"variable":var,"claim_type":"supporting_commentary","quoted_span":span,"confidence":"medium","extraction_method":"deterministic_semantic_rules","requires_quality_gate":True})
    return extractions

def build_semantic_report(chunks,ticker=TARGET_REVIEW_TICKER):
    all_extractions=[]
    for c in chunks: all_extractions.extend(extract_semantic(c))
    vars_extracted=sorted(set(e["variable"] for e in all_extractions))
    return {"generated_at":now_ts(),"ticker":normalize_ticker(ticker),"semantic_extractions":{"chunks_checked":len(chunks),"semantic_extractions":len(all_extractions),"variables_extracted":vars_extracted,"rows":all_extractions,"pending_created":0,"paper_order_created":0},"safety":{"extraction_does_not_confirm":True,"extraction_uses_only_deterministic_rules":True}}
