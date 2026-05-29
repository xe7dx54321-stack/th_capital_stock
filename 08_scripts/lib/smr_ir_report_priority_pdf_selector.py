#!/usr/bin/env python3
"""IR/Report priority PDF selector - Phase 67."""
from typing import Any
from smr_business_disclosure_relevance_scorer import score_disclosures
from smr_administrative_disclosure_filter import is_administrative_or_legal

IR_REPORT_PRIORITY={"investor_relations_record":100,"annual_report":90,"semiannual_report":85,"quarterly_report":80,"performance_briefing_or_earnings_call":75,"major_announcement":50,"other_announcement":20}

def select_ir_report_pdfs(rows:list[dict],max_pdfs:int=25)->dict[str,Any]:
    candidates=[]
    for rw in rows:
        ttl=(rw.get("title","") or "")
        if not rw.get("pdf_url_available",False): continue
        if is_administrative_or_legal(ttl):
            kw=rw.get("keyword_groups_hit",[]) or []
            if not kw: continue
        st=rw.get("source_type","other_announcement")
        base=IR_REPORT_PRIORITY.get(st,20)
        biz_hits=sum(1 for kw in ["800G","1.6T","光模块","客户需求","订单","产能","出货"] if kw.lower() in ttl.lower())
        score=min(base+biz_hits*5,99)
        reasons=[st.replace("_"," ")]
        if biz_hits: reasons.append("business_keyword_hit")
        if "投资者关系" in ttl: reasons.append("IR_record")
        if "年度报告" in ttl: reasons.append("annual_report")
        candidates.append({"source_id":rw.get("source_id",""),"source_type":st,"title":ttl[:80],"adjunct_url":rw.get("adjunct_url",""),"relevance_score":score,"selection_reason":reasons})
    candidates.sort(key=lambda x:-x["relevance_score"])
    selected=candidates[:max_pdfs]
    breakdown={}
    for s in selected: breakdown[s["source_type"]]=breakdown.get(s["source_type"],0)+1
    admin_filtered=sum(1 for rw in rows if is_administrative_or_legal(rw.get("title","") or ""))
    return {"candidate_pdfs":len(candidates),"selected_pdfs":len(selected),"selected_breakdown":breakdown,"administrative_legal_filtered":admin_filtered,"rows":selected}
