#!/usr/bin/env python3
"""Phase 67 high-value PDF pool loader."""
from typing import Any
from smr_cninfo_pagination_query_engine import query_paginated
from smr_administrative_disclosure_filter import is_administrative_or_legal, ADMIN_PATTERNS

HIGH_VALUE_TYPES={"investor_relations_record":100,"performance_briefing_or_earnings_call":95,"annual_report":90,"semiannual_report":85,"quarterly_report":80,"major_announcement":55}

def load_high_value_pool(ticker="300308.SZ",max_pages=5,page_size=30,max_pdfs=25)->dict[str,Any]:
    r={"ticker":ticker,"phase67b_high_value_pdf_pool":{"source_pool_loaded":False,"candidate_pdfs":0,"high_value_pdfs":0,"source_type_breakdown":{},"administrative_legal_excluded":0,"all_have_pdf_url":True,"mock_used":False,"fixture_used":False,"rows":[]}}
    p=r["phase67b_high_value_pdf_pool"]
    try:
        pq=query_paginated(ticker,max_pages,page_size,mode="execute")
        rows=pq.get("cninfo_pagination_inventory",{}).get("rows",[])
        p["source_pool_loaded"]=True;p["candidate_pdfs"]=len(rows)
        high_value=[];admin_excluded=0;breakdown={}
        for rw in rows:
            adj=rw.get("adjunct_url","")
            if not adj: continue
            if is_administrative_or_legal(rw.get("title","")):
                admin_excluded+=1;continue
            st=rw.get("source_type","other_announcement")
            priority=HIGH_VALUE_TYPES.get(st,20)
            if priority<50: continue
            high_value.append({**rw,"priority":priority})
            breakdown[st]=breakdown.get(st,0)+1
        high_value.sort(key=lambda x:-x["priority"])
        selected=high_value[:max_pdfs]
        p["high_value_pdfs"]=len(selected)
        p["source_type_breakdown"]=breakdown
        p["administrative_legal_excluded"]=admin_excluded
        p["all_have_pdf_url"]=all(r.get("adjunct_url") for r in selected)
        p["rows"]=selected;p["status"]="ok"
    except Exception as e: p["status"]="error:"+str(e)[:80]
    return r
