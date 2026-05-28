#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import generate_execution_id, now_ts
import re

def normalize_text(text,source_id,source_type,ticker):
    text=re.sub(r'\s+',' ',text).strip()
    meta="metadata-derived" if "metadata" in text.lower()[:30] else "fixture"
    is_short=len(text)<30
    return {"normalized_text_id":generate_execution_id(f"norm_text_{normalize_ticker(ticker).split('.')[0]}"),"source_id":source_id,"source_type":source_type,"text_chars":len(text),"preserved_structure":["qa_section"] if "Q:" in text else ["general_text"],"text_quality":"usable" if not is_short else "too_short","text_origin":meta,"too_short":is_short}

def build_normalization_report(texts,ticker=TARGET_REVIEW_TICKER):
    norm=[normalize_text(t.get("content",""),t.get("source_id",""),t.get("source_type",""),ticker) for t in texts]
    usable=[n for n in norm if not n["too_short"]]
    return {"generated_at":now_ts(),"ticker":normalize_ticker(ticker),"text_normalization_report":{"texts_checked":len(texts),"normalized_texts":len(usable),"too_short":len(norm)-len(usable),"metadata_derived":sum(1 for n in norm if n["text_origin"]=="metadata-derived"),"sample_fixture_texts":sum(1 for n in norm if n["text_origin"]=="fixture"),"rows":norm}}
