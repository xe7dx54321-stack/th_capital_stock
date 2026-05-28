#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import generate_execution_id, now_ts

CHUNK_TYPES = {"qa_section","management_commentary","product_business_description","order_visibility_commentary","shipment_delivery_commentary","financial_section","risk_section","general_text","unknown"}

def chunk_text(normalized_text):
    sid=normalized_text.get("normalized_text_id",""); tid=normalized_text.get("source_id","")
    text=normalized_text.get("content",""); ctype="general_text"
    if len(text)<30: ctype="unknown"
    elif "Q:" in text: ctype="qa_section"
    elif "订单" in text: ctype="order_visibility_commentary"
    elif "出货" in text or "shipment" in text.lower(): ctype="shipment_delivery_commentary"
    elif "产品" in text or "高端" in text: ctype="product_business_description"
    elif "营收" in text or "利润" in text: ctype="financial_section"
    elif "风险" in text: ctype="risk_section"
    chunk_text_segment=text[:800] if len(text)>800 else text
    return {"chunk_id":generate_execution_id(f"chunk_{normalize_ticker(normalized_text.get('ticker','300308.SZ')).split('.')[0]}"),"source_id":tid,"normalized_text_id":sid,"chunk_type":ctype,"text_chars":len(chunk_text_segment),"quoted_span_possible":ctype!="unknown" and ctype!="general_text" and len(text)>=30}

def build_chunks_from_texts(normalized_texts,ticker=TARGET_REVIEW_TICKER):
    chunks=[chunk_text(t) for t in normalized_texts if not t.get("too_short")]
    types={}; 
    for c in chunks: k=c["chunk_type"]; types[k]=types.get(k,0)+1
    return {"generated_at":now_ts(),"ticker":normalize_ticker(ticker),"real_source_chunks":{"normalized_texts_checked":len(normalized_texts),"chunks_created":len(chunks),"chunk_type_breakdown":types,"rows":chunks}}
