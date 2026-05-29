#!/usr/bin/env python3
"""Priority PDF selector - Phase 66."""
from typing import Any
from smr_business_keyword_hit_scanner import scan_title

SOURCE_PRIORITY={"investor_relations_record":95,"annual_report":80,"semiannual_report":75,"quarterly_report":70,"performance_briefing_or_earnings_call":85,"major_announcement":65,"other_announcement":30}

def select_priority_pdfs(rows:list[dict],max_pdfs:int=15)->dict[str,Any]:
    candidates=[];seen_titles=set()
    for row in rows:
        ttl=(row.get("title","") or "")
        if ttl in seen_titles: continue
        seen_titles.add(ttl)
        if not row.get("pdf_url_available",False): continue
        st=row.get("source_type","other_announcement")
        base_score=SOURCE_PRIORITY.get(st,30)
        ts=scan_title(ttl)
        kw_bonus=ts.get("hit_count",0)*10
        priority_score=min(base_score+kw_bonus,99)
        reasons=[st.replace("_"," ")]
        if ts["title_hit"]: reasons.append("keyword hit: "+",".join(ts.get("keywords",[])[:3]))
        candidates.append({"source_id":row.get("source_id",""),"source_type":st,"title":ttl[:80],"priority_score":priority_score,"selection_reason":reasons})
    candidates.sort(key=lambda x:-x["priority_score"])
    selected=candidates[:max_pdfs]
    breakdown={};[breakdown.update({s["source_type"]:breakdown.get(s["source_type"],0)+1}) for s in selected]
    return {"candidate_pdfs":len(candidates),"selected_pdfs":len(selected),"selection_reason_breakdown":breakdown,"rows":selected}
