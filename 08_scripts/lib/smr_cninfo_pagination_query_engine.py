#!/usr/bin/env python3
"""CNINFO pagination query engine - Phase 67."""
import json,urllib.request,urllib.parse
from typing import Any
from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES

CNINFO_API="https://www.cninfo.com.cn/new/hisAnnouncement/query"
HEADERS={"User-Agent":"Mozilla/5.0","Accept":"application/json","Referer":"https://www.cninfo.com.cn/","Content-Type":"application/x-www-form-urlencoded"}

def query_paginated(ticker="300308.SZ",max_pages=5,page_size=30,skip_network=False,mode="execute")->dict[str,Any]:
    curated=CURATED_CNINFO_IDENTITIES.get(ticker,{})
    org_id=curated.get("org_id","")
    code=curated.get("security_code",ticker.split(".")[0])
    stock_param=code+","+org_id if org_id else code
    r={"ticker":ticker,"cninfo_pagination_inventory":{"identity_map_used":bool(org_id),"stock_param":stock_param,"pages_requested":max_pages,"pages_succeeded":0,"page_size":page_size,"metadata_rows_collected":0,"metadata_rows_after_dedupe":0,"duplicate_rows_removed":0,"source_type_breakdown":{},"raw_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False,"rows":[]}}
    inv=r["cninfo_pagination_inventory"]
    if mode in ("dry-run","dry_run"): inv["status"]="dry_run";return r
    if skip_network: inv["status"]="skipped_network_disabled";return r
    all_rows=[];seen_ids=set();pages_ok=0
    try:
        for page in range(1,max_pages+1):
            params={"pageNum":page,"pageSize":page_size,"stock":stock_param,"plate":curated.get("plate","sz"),"column":curated.get("column","szse"),"tabName":"fulltext","searchkey":"","secid":"","category":"","trade":"","seDate":""}
            data=urllib.parse.urlencode(params).encode()
            req=urllib.request.Request(CNINFO_API,data=data,headers=dict(HEADERS))
            try:
                with urllib.request.urlopen(req,timeout=20) as resp:
                    body=json.loads(resp.read().decode("utf-8",errors="replace"))
                anns=body.get("announcements",[])
                if not anns: continue
                pages_ok+=1
                for a in anns:
                    sid=str(a.get("announcementId",""))
                    ttl=(a.get("announcementTitle","") or "")
                    dedupe_key=sid+"|"+ttl[:40]
                    if dedupe_key in seen_ids: continue
                    seen_ids.add(dedupe_key)
                    adj=a.get("adjunctUrl","")
                    if "投资者关系" in ttl or "调研" in ttl: st="investor_relations_record"
                    elif "年度报告" in ttl: st="annual_report"
                    elif "半年度" in ttl: st="semiannual_report"
                    elif "季度报告" in ttl or "季报" in ttl: st="quarterly_report"
                    elif "业绩说明" in ttl or "业绩预告" in ttl or "业绩快报" in ttl: st="performance_briefing_or_earnings_call"
                    elif "重大" in ttl or "扩产" in ttl or "投资" in ttl: st="major_announcement"
                    else: st="other_announcement"
                    all_rows.append({"source_id":"cninfo_"+code+"_"+sid,"title":ttl,"source_type":st,"pdf_url_available":bool(adj),"adjunct_url":adj,"publish_date":str(a.get("announceTime","")),"page":page})
            except Exception: pass
        inv["pages_succeeded"]=pages_ok
        inv["metadata_rows_collected"]=len(all_rows)
        inv["metadata_rows_after_dedupe"]=len(all_rows)
        inv["duplicate_rows_removed"]=0
        bd={}
        for rw in all_rows:
            st=rw.get("source_type","")
            bd[st]=bd.get(st,0)+1
        inv["source_type_breakdown"]=bd
        inv["rows"]=all_rows
        inv["pdf_urls_available"]=sum(1 for rw in all_rows if rw.get("pdf_url_available"))
        inv["status"]="ok" if pages_ok>0 else "degraded_no_pages"
    except Exception as e:
        inv["status"]="error:"+str(e)[:100]
    return r
