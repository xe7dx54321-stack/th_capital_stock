#!/usr/bin/env python3
"""Real disclosure text quality classifier - Phase 65b."""
from __future__ import annotations
import hashlib,re
from typing import Any

BUSINESS_KEYWORDS=["800G","1.6T","光模块","光器件","高速率","产能","出货","订单","客户","份额","毛利率","ASP","均价","收入","盈利"]
MIN_TEXT_LENGTH=200

def classify_text(source_id:str,title:str,text:str|None,source_type:str="")->dict[str,Any]:
    if not text:
        return {"source_id":source_id,"quality_status":"metadata_only_not_evidence","text_length":0,"business_keyword_hit":False,"allowed_usage":"do_not_use"}
    text_len=len(text);text_hash=hashlib.sha256(text.encode()).hexdigest()
    is_chinese=bool(re.search(r"[\u4e00-\u9fff]",text))
    has_keywords=any(kw in text for kw in BUSINESS_KEYWORDS)
    status="usable_for_business_evidence"
    if text_len<MIN_TEXT_LENGTH: status="too_short_not_evidence"
    elif not is_chinese: status="usable_with_warnings"
    elif not has_keywords: status="financial_report_text_only" if source_type in ("annual_report","quarterly_report") else "usable_with_warnings"
    usage="real_business_source_text" if status=="usable_for_business_evidence" else ("metadata_only_not_evidence" if status in ("too_short_not_evidence","metadata_only_not_evidence") else "usable_with_warnings")
    return {"source_id":source_id,"title":title[:80],"quality_status":status,"text_length":text_len,"text_hash":text_hash[:16],"language_is_chinese":is_chinese,"business_keyword_hit":has_keywords,"source_type":source_type,"allowed_usage":usage}

def build_quality_report(ticker:str,texts:list[dict],skip:bool=False)->dict[str,Any]:
    checked=[];usable=0;warnings=0;meta_only=0;too_short=0
    for t in texts:
        c=classify_text(t.get("source_id",""),t.get("title",""),t.get("text"),t.get("source_type",""))
        checked.append(c)
        if c["quality_status"]=="usable_for_business_evidence": usable+=1
        elif c["quality_status"]=="usable_with_warnings": warnings+=1
        elif c["quality_status"]=="metadata_only_not_evidence": meta_only+=1
        elif c["quality_status"]=="too_short_not_evidence": too_short+=1
    return {"ticker":ticker,"real_disclosure_text_quality":{"texts_checked":len(checked),"usable_for_business_evidence":usable,"usable_with_warnings":warnings,"metadata_only_not_evidence":meta_only,"too_short_not_evidence":too_short,"rows":checked,"mock_used":False,"fixture_used":False}}
