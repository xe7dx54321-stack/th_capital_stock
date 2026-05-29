#!/usr/bin/env python3
"""Business disclosure relevance scorer - Phase 67."""
from typing import Any
from smr_administrative_disclosure_filter import is_administrative_or_legal

SOURCE_PRIORITY={"investor_relations_record":95,"performance_briefing_or_earnings_call":90,"annual_report":85,"semiannual_report":80,"quarterly_report":75,"major_announcement":60,"other_announcement":30}

BIZ_KEYWORDS=["800G","1.6T","1.6 T","光模块","硅光","CPO","LPO","出货","交付","客户需求","订单","能见度","产能","扩产","产品结构","高端产品","ASP","毛利率","海外客户","云厂商"]

def score_disclosure(title:str,source_type:str,has_pdf:bool,searchkey_hit:bool=False)->dict[str,Any]:
    score=SOURCE_PRIORITY.get(source_type,30)
    reasons=[source_type.replace("_"," ")]
    if is_administrative_or_legal(title):
        score-=30;reasons.append("administrative_legal_penalty")
    if searchkey_hit:
        score+=10;reasons.append("searchkey_hit")
    biz_hits=[kw for kw in BIZ_KEYWORDS if kw.lower() in (title or "").lower()]
    if biz_hits:
        score+=len(biz_hits)*5;reasons.append("business_keyword: "+",".join(biz_hits[:3]))
    if has_pdf: score+=5;reasons.append("pdf_available")
    else: score-=10
    if "投资者关系" in title or "调研" in title: score+=15;reasons.append("ir_record_detected")
    if "年度报告" in title: score+=10;reasons.append("annual_report_detected")
    score=max(0,min(score,99))
    if score>=80: relevance="high_relevance"
    elif score>=55: relevance="medium_relevance"
    else: relevance="low_relevance"
    return {"relevance_score":score,"relevance":relevance,"relevance_reasons":reasons}

def score_disclosures(rows:list[dict])->dict[str,Any]:
    scored=[];high=0;medium=0;low=0;breakdown={}
    for rw in rows:
        s=score_disclosure(rw.get("title",""),rw.get("source_type","other"),rw.get("pdf_url_available",False),bool(rw.get("searchkey","")))
        s["source_id"]=rw.get("source_id","");s["title"]=(rw.get("title","") or "")[:80]
        s["source_type"]=rw.get("source_type","")
        scored.append(s)
        if s["relevance"]=="high_relevance": high+=1
        elif s["relevance"]=="medium_relevance": medium+=1
        else: low+=1
        bd_key=rw.get("source_type","other")
        breakdown[bd_key]=breakdown.get(bd_key,0)+1
    scored.sort(key=lambda x:-x["relevance_score"])
    return {"disclosures_scored":len(scored),"high_relevance":high,"medium_relevance":medium,"low_relevance":low,"score_breakdown":breakdown,"top_ranked":scored[:20]}
