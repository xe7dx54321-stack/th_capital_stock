#!/usr/bin/env python3
"""Phase 67b IR/report text quality classifier."""
from typing import Any
def classify_67b_text(rows:list[dict])->dict[str,Any]:
    results=[];grades={};usable=0
    for rw in rows:
        if rw.get("text_extraction_status")!="pdf_text_ok": continue
        st=rw.get("source_type","other");tl=rw.get("text_length",0);kws=rw.get("keyword_groups_hit",[])
        title=rw.get("title","") or "";score=50
        if st=="investor_relations_record": score+=25
        elif st=="performance_briefing_or_earnings_call": score+=20
        elif st in ("annual_report","semiannual_report","quarterly_report"): score+=15
        if tl>5000: score+=10
        elif tl<500: score-=20
        if kws: score+=len(kws)*8
        score=max(0,min(score,99))
        if score>=80: grade="high_signal_ir_text"
        elif score>=65: grade="usable_ir_text"
        elif score>=50: grade="usable_report_text"
        elif score>=35: grade="financial_report_context"
        else: grade="low_signal"
        grades[grade]=grades.get(grade,0)+1
        if grade in ("high_signal_ir_text","usable_ir_text","usable_report_text"): usable+=1
        results.append({"source_id":rw.get("source_id",""),"title":title[:80],"source_type":st,"quality_grade":grade,"score":score,"text_length":tl,"keyword_groups_hit":kws,"usable_for_deep":grade in ("high_signal_ir_text","usable_ir_text","usable_report_text")})
    return {"texts_checked":len(results),"high_signal_ir_text":grades.get("high_signal_ir_text",0),"usable_ir_text":grades.get("usable_ir_text",0),"usable_report_text":grades.get("usable_report_text",0),"financial_report_context":grades.get("financial_report_context",0),"low_signal":grades.get("low_signal",0),"texts_usable_for_deep_extraction":usable,"rows":sorted(results,key=lambda x:-x["score"])}
