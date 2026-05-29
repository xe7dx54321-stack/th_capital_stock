#!/usr/bin/env python3
"""Administrative/legal disclosure filter - Phase 67."""
from typing import Any

ADMIN_PATTERNS=[
    "股权激励","限制性股票","股票期权","归属价格","归属条件",
    "独立董事","监事会","董事会决议","法律意见书","律师事务所",
    "公告编号","减持","质押","回购","公司章程","股东大会",
    "更正公告","提示性公告","核查意见","法律意见",
]

def is_administrative_or_legal(title:str)->bool:
    t=(title or "").lower()
    return any(p in t for p in ADMIN_PATTERNS)

def filter_disclosures(rows:list[dict])->dict[str,Any]:
    checked=0;admin_detected=0;filtered_out=0;downgraded=0;retained=0
    result_rows=[]
    for rw in rows:
        checked+=1;title=rw.get("title","") or ""
        if is_administrative_or_legal(title):
            admin_detected+=1
            keywords=rw.get("keyword_groups_hit",[]) or rw.get("keyword_groups_hit",[])
            has_biz_kw=keywords and len(keywords)>0 and any(k!="asp_price" for k in keywords)
            if has_biz_kw:
                result_rows.append({**rw,"filter_status":"downgraded_to_review_required","filter_reason":"administrative_legal_but_has_business_keyword","blocked_interpretation":"product_asp_signal" if "asp_price" in str(keywords) else None})
                downgraded+=1
            else:
                result_rows.append({**rw,"filter_status":"filtered_out","filter_reason":"administrative_or_legal_no_business_keyword","blocked_interpretation":"product_asp_signal" if "价格" in title else None})
                filtered_out+=1
        else:
            result_rows.append({**rw,"filter_status":"retained"})
            retained+=1
    return {"metadata_checked":checked,"administrative_or_legal_detected":admin_detected,"filtered_out":filtered_out,"downgraded_to_review_required":downgraded,"business_disclosures_retained":retained,"rows":result_rows}
