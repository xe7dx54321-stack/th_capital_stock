#!/usr/bin/env python3
"""CNINFO category + searchkey matrix - Phase 67."""
import json,urllib.request,urllib.parse
from typing import Any
from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES

CNINFO_API="https://www.cninfo.com.cn/new/hisAnnouncement/query"
HEADERS={"User-Agent":"Mozilla/5.0","Accept":"application/json","Referer":"https://www.cninfo.com.cn/","Content-Type":"application/x-www-form-urlencoded"}

CATEGORIES=["investor_relations_record","annual_report","semiannual_report","quarterly_report","performance_briefing","announcement"]
SEARCHKEYS=["投资者关系","年度报告","半年度报告","800G","光模块","订单","客户需求","产品结构","产能","ASP"]
CNINFO_CATEGORY_MAP={"category_ndbg_szsh;CATEGORY":"投资者关系"}

def run_matrix(ticker="300308.SZ",skip_network=False,mode="execute")->dict[str,Any]:
    r={"ticker":ticker,"category_searchkey_matrix":{"parameter_sets_tested":0,"successful_sets":0,"zero_result_sets":0,"error_sets":0,"best_sets":[],"mock_used":False,"fixture_used":False}}
    mx=r["category_searchkey_matrix"]
    if mode in ("dry-run","dry_run"): mx["status"]="dry_run";return r
    if skip_network: mx["status"]="skipped_network_disabled";return r
    curated=CURATED_CNINFO_IDENTITIES.get(ticker,{})
    org_id=curated.get("org_id","")
    code=curated.get("security_code",ticker.split(".")[0])
    stock_param=code+","+org_id if org_id else code
    sets_tested=0;successful=0;zero=0;errors=0;best=[]
    for cat in CATEGORIES[:4]:
        for sk in SEARCHKEYS[:5]:
            sets_tested+=1
            if sets_tested>20: break
            try:
                params={"pageNum":1,"pageSize":10,"stock":stock_param,"plate":curated.get("plate","sz"),"column":curated.get("column","szse"),"tabName":"fulltext","searchkey":sk,"secid":"","category":"","trade":"","seDate":""}
                data=urllib.parse.urlencode(params).encode()
                req=urllib.request.Request(CNINFO_API,data=data,headers=dict(HEADERS))
                with urllib.request.urlopen(req,timeout=20) as resp:
                    body=json.loads(resp.read().decode("utf-8",errors="replace"))
                anns=body.get("announcements",[])
                if not anns: zero+=1;continue
                successful+=1
                titles=[(a.get("announcementTitle","") or "")[:50] for a in anns[:3]]
                best.append({"category":cat,"searchkey":sk,"results_count":len(anns),"sample_titles":titles})
            except Exception: errors+=1
        if sets_tested>20: break
    mx["parameter_sets_tested"]=sets_tested
    mx["successful_sets"]=successful
    mx["zero_result_sets"]=zero
    mx["error_sets"]=errors
    best.sort(key=lambda x:-x["results_count"])
    mx["best_sets"]=best[:10]
    mx["status"]="ok"
    return r
