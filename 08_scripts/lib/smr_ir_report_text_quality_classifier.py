#!/usr/bin/env python3
"""IR/Report text quality classifier - Phase 67."""
from typing import Any
from smr_administrative_disclosure_filter import is_administrative_or_legal

QUALITY_GRADES=["high_signal_ir_text","usable_ir_text","usable_report_text","financial_report_context","administrative_text","low_signal","rejected"]

def classify_ir_report_text(title:str,source_type:str,text_len:int,kw_groups:list,has_qa:bool=False)->dict[str,Any]:
    score=50;reasons=[]
    if text_len>5000: score+=15;reasons.append("substantial_text")
    elif text_len>2000: score+=5
    else: score-=15;reasons.append("short_text")
    if source_type=="investor_relations_record": score+=20;reasons.append("ir_record")
    elif source_type in ("annual_report","semiannual_report","quarterly_report"): score+=10;reasons.append("financial_report")
    if has_qa: score+=10;reasons.append("qa_structure")
    if kw_groups:
        score+=len(kw_groups)*8;reasons.append("business_kw: "+",".join(kw_groups[:3]))
    else:
        score-=10;reasons.append("no_business_keywords")
    if is_administrative_or_legal(title):
        score-=25;reasons.append("administrative_or_legal")
    score=max(0,min(score,99))
    if score>=80: grade="high_signal_ir_text"
    elif score>=65: grade="usable_ir_text"
    elif score>=50 and source_type in ("annual_report","semiannual_report","quarterly_report"): grade="usable_report_text"
    elif score>=50: grade="usable_ir_text"
    elif score>=40 and source_type in ("annual_report","semiannual_report","quarterly_report"): grade="financial_report_context"
    elif is_administrative_or_legal(title): grade="administrative_text"
    elif score>=30: grade="low_signal"
    else: grade="rejected"
    return {"quality_grade":grade,"score":score,"reasons":reasons,"usable_for_deep":grade in ("high_signal_ir_text","usable_ir_text","usable_report_text")}

def classify_texts(rows:list[dict])->dict[str,Any]:
    results=[];grades={g:0 for g in QUALITY_GRADES};usable=0
    for rw in rows:
        if rw.get("text_extraction_status")!="pdf_text_ok": continue
        q=classify_ir_report_text(rw.get("title",""),rw.get("source_type","other"),rw.get("text_length",0),rw.get("keyword_groups_hit",[]))
        q["source_id"]=rw.get("source_id","");q["title"]=(rw.get("title","") or "")[:80]
        grades[q["quality_grade"]]=grades.get(q["quality_grade"],0)+1
        if q["usable_for_deep"]: usable+=1
        results.append(q)
    return {"texts_checked":len(results),"high_signal_ir_text":grades.get("high_signal_ir_text",0),"usable_ir_text":grades.get("usable_ir_text",0),"usable_report_text":grades.get("usable_report_text",0),"financial_report_context":grades.get("financial_report_context",0),"administrative_text":grades.get("administrative_text",0),"low_signal":grades.get("low_signal",0),"rejected":grades.get("rejected",0),"texts_usable_for_deep_extraction":usable,"rows":sorted(results,key=lambda x:-x["score"])}
