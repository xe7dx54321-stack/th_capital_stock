#!/usr/bin/env python3
"""Targeted CNINFO metadata harvester - Phase 66."""
import json,urllib.request,urllib.parse
from typing import Any
from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
from smr_cninfo_targeted_disclosure_category_planner import get_priority_order

CNINFO_API="https://www.cninfo.com.cn/new/hisAnnouncement/query"
HEADERS={"User-Agent":"Mozilla/5.0","Accept":"application/json","Referer":"https://www.cninfo.com.cn/","Content-Type":"application/x-www-form-urlencoded"}

def harvest_targeted_metadata(ticker="300308.SZ",max_metadata=50,skip_network=False,mode="execute")->dict[str,Any]:
    curated=CURATED_CNINFO_IDENTITIES.get(ticker,{});org_id=curated.get("org_id","")
    code=curated.get("security_code",ticker.split(".")[0]);stock_param=code+","+org_id if org_id else code
    r={"ticker":ticker,"cninfo_targeted_metadata_inventory":{"identity_map_used":bool(org_id),"stock_param":stock_param,"metadata_sources_found":0,"targeted_metadata_selected":0,"category_breakdown":{},"pdf_urls_available":0,"raw_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False,"rows":[]}}
    inv=r["cninfo_targeted_metadata_inventory"]
    if mode in ("dry-run","dry_run"): inv["status"]="dry_run";return r
    if skip_network: inv["status"]="skipped_network_disabled";return r
    try:
        params={"pageNum":1,"pageSize":min(max_metadata,30),"stock":stock_param,"plate":curated.get("plate","sz"),"column":curated.get("column","szse"),"tabName":"fulltext","searchkey":"","secid":"","category":"","trade":"","seDate":""}
        data=urllib.parse.urlencode(params).encode()
        req=urllib.request.Request(CNINFO_API,data=data,headers=dict(HEADERS))
        with urllib.request.urlopen(req,timeout=20) as resp:
            body=json.loads(resp.read().decode("utf-8",errors="replace"))
        inv["metadata_sources_found"]=body.get("totalAnnouncement",0)
        anns=body.get("announcements",[])
        categories={};pdf_count=0;selected=[]
        for a in anns[:max_metadata]:
            ttl=(a.get("announcementTitle","") or "");adj=a.get("adjunctUrl","")
            if "投资者关系" in ttl or "调研" in ttl: st="investor_relations_record"
            elif "年度报告" in ttl: st="annual_report"
            elif "半年度" in ttl: st="semiannual_report"
            elif "季度报告" in ttl or "季报" in ttl: st="quarterly_report"
            elif "业绩说明" in ttl or "业绩预告" in ttl or "业绩快报" in ttl: st="performance_briefing_or_earnings_call"
            elif "重大" in ttl or "扩产" in ttl or "投资" in ttl: st="major_announcement"
            else: st="other_announcement"
            categories[st]=categories.get(st,0)+1
            if adj: pdf_count+=1
            selected.append({"source_id":"cninfo_"+code+"_"+str(a.get("announcementId","")),"title":ttl,"source_type":st,"pdf_url_available":bool(adj),"adjunct_url":adj,"publish_date":str(a.get("announceTime",""))})
        inv["category_breakdown"]=categories;inv["pdf_urls_available"]=pdf_count;inv["targeted_metadata_selected"]=len(selected);inv["rows"]=selected;inv["status"]="ok"
    except Exception as e: inv["status"]="error";inv["failure_reason"]=str(e)[:100]
    return r
