#!/usr/bin/env python3
"""Business keyword hit scanner - Phase 66."""
import json,re
from pathlib import Path
from typing import Any

KW_PATH=Path(__file__).resolve().parent.parent.parent/"config"/"ai_optical_business_keywords.json"

def load_keywords()->dict[str,list[str]]:
    if not KW_PATH.exists(): return {}
    with open(KW_PATH,"r",encoding="utf-8-sig") as f: return json.load(f)

def scan_title(title:str)->dict[str,Any]:
    kw=load_keywords();hits={};all_hits=[]
    for group,words in kw.items():
        matched=[w for w in words if w.lower() in (title or "").lower()]
        if matched: hits[group]=matched;all_hits.extend(matched)
    return {"title_hit":len(all_hits)>0,"keyword_groups":list(hits.keys()),"keywords":all_hits,"hit_count":len(all_hits)}

def scan_text(text:str)->dict[str,Any]:
    kw=load_keywords();hits={};all_hits=[]
    for group,words in kw.items():
        matched=[w for w in words if w.lower() in (text or "").lower()]
        if matched: hits[group]=matched;all_hits.extend(matched)
    return {"text_hit":len(all_hits)>0,"keyword_groups":list(hits.keys()),"keywords":all_hits,"hit_count":len(all_hits)}

def scan_metadata_rows(rows:list[dict])->dict[str,Any]:
    scanned=0;hits=0;results=[];breakdown={}
    for row in rows:
        scanned+=1;ts=scan_title(row.get("title",""))
        if ts["title_hit"]:
            hits+=1;score=min(ts["hit_count"]*15+50,99)
            for g in ts["keyword_groups"]: breakdown[g]=breakdown.get(g,0)+1
            results.append({"source_id":row.get("source_id",""),"title":(row.get("title","") or "")[:80],"keyword_groups_hit":ts["keyword_groups"],"keywords_hit":ts["keywords"],"priority_score":score,"allowed_usage":"priority_pdf_text_extraction"})
    return {"sources_scanned":scanned,"sources_with_keyword_hit":hits,"high_priority_hits":hits,"keyword_group_breakdown":breakdown,"rows":sorted(results,key=lambda x:-x["priority_score"])}
