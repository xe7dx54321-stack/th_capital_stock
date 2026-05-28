#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_real_source_text_availability import SOURCE_TEXT_MAP
from smr_wiki import now_ts

def extract_text_from_source(source,mode="dry-run",skip_download=True):
    st=source.get("source_type","unknown"); info=SOURCE_TEXT_MAP.get(st)
    if not info: return ("",None,{},False)
    text,_,_ = info
    if mode=="execute" and not skip_download:
        return (text, {"text":"extracted","quality":"fixture"} ,{} ,text!="")
    return (text, {"text":"fixture","quality":"readable"}, {"cache_saved":"dry_run_only"}, len(text)>0)

def build_extraction_result(sources,ticker=TARGET_REVIEW_TICKER,mode="dry-run",skip_download=True):
    texts=[]; total_chars=0; metadata_only=0; extracted=0; skipped=0
    for s in sources:
        text,meta,cache,ok=extract_text_from_source(s,mode,skip_download)
        if ok: extracted+=1; total_chars+=len(text); texts.append({"source_id":s.get("source_id"),"text_chars":len(text),"cache_written":mode=="execute" and not skip_download,"extraction_ok":True})
        elif text: metadata_only+=1; texts.append({"source_id":s.get("source_id"),"text_chars":len(text),"cache_written":False,"extraction_ok":False,"reason":"metadata_summary_only"})
        else: skipped+=1
    return {"generated_at":now_ts(),"ticker":normalize_ticker(ticker),"controlled_text_extraction":{"mode":mode,"sources_checked":len(sources),"text_extracted":extracted,"metadata_summary_only":metadata_only,"download_skipped":skipped,"raw_content_saved":False,"text_cache_written":0,"text_cache_ignored_by_git":True,"total_text_chars":total_chars,"pending_created":0,"paper_order_created":0,"real_trade_created":0},"safety":{"no_raw_saved":True,"text_cache_not_committed":True}}
