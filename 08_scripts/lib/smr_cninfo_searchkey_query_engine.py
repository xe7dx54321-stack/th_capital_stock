#!/usr/bin/env python3
"""CNINFO searchkey query engine - Phase 67."""
import json,urllib.request,urllib.parse
from typing import Any
from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES

CNINFO_API="https://www.cninfo.com.cn/new/hisAnnouncement/query"
HEADERS={"User-Agent":"Mozilla/5.0","Accept":"application/json","Referer":"https://www.cninfo.com.cn/","Content-Type":"application/x-www-form-urlencoded"}

SEARCHKEY_GROUPS={
    "document_type":["投资者关系","投资者关系活动记录","业绩说明会","年度报告","半年度报告","季度报告"],
    "product_generation":["800G","1.6T","光模块","高速光模块","硅光","CPO","LPO"],
    "business_driver":["订单","客户需求","海外客户","AI客户","云厂商","产品结构","高端产品","出货","交付","产能","扩产"],
    "pricing_margin":["ASP","价格","毛利率"],
}

def query_by_searchkeys(ticker="300308.SZ",max_results=120,skip_network=False,mode="execute")->dict[str,Any]:
    curated=CURATED_CNINFO_IDENTITIES.get(ticker,{})
    org_id=curated.get("org_id","")
    code=curated.get("security_code",ticker.split(".")[0])
    stock_param=code+","+org_id if org_id else code
    r={"ticker":ticker,"cninfo_searchkey_inventory":{"identity_map_used":bool(org_id),"stock_param":stock_param,"searchkey_queries_run":0,"metadata_rows_collected":0,"metadata_rows_after_dedupe":0,"keyword_group_breakdown":{},"top_hits":[],"raw_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False,"rows":[]}}
    inv=r["cninfo_searchkey_inventory"]
    if mode in ("dry-run","dry_run"): inv["status"]="dry_run";return r
    if skip_network: inv["status"]="skipped_network_disabled";return r
    all_rows=[];seen_ids=set();queries_run=0;group_count={}
    try:
        for group_name,keywords in SEARCHKEY_GROUPS.items():
            for sk in keywords:
                queries_run+=1
                if queries_run>60: break
                if len(all_rows)>=max_results*3: break
                params={"pageNum":1,"pageSize":15,"stock":stock_param,"plate":curated.get("plate","sz"),"column":curated.get("column","szse"),"tabName":"fulltext","searchkey":sk,"secid":"","category":"","trade":"","seDate":""}
                data=urllib.parse.urlencode(params).encode()
                req=urllib.request.Request(CNINFO_API,data=data,headers=dict(HEADERS))
                try:
                    with urllib.request.urlopen(req,timeout=20) as resp:
                        body=json.loads(resp.read().decode("utf-8",errors="replace"))
                    for a in body.get("announcements",[]):
                        sid=str(a.get("announcementId",""))
                        ttl=(a.get("announcementTitle","") or "")
                        dedupe_key=sid
                        if dedupe_key in seen_ids: continue
                        seen_ids.add(dedupe_key)
                        adj=a.get("adjunctUrl","")
                        if "投资者关系" in ttl or "调研" in ttl: st="investor_relations_record"
                        elif "年度报告" in ttl: st="annual_report"
                        elif "半年度" in ttl: st="semiannual_report"
                        elif "季度报告" in ttl or "季报" in ttl: st="quarterly_report"
                        elif "业绩说明" in ttl or "业绩预告" in ttl or "业绩快报" in ttl: st="performance_briefing_or_earnings_call"
                        elif "重大" in ttl or "扩产" in ttl: st="major_announcement"
                        else: st="other_announcement"
                        row={"source_id":"cninfo_"+code+"_"+sid,"title":ttl,"source_type":st,"pdf_url_available":bool(adj),"adjunct_url":adj,"publish_date":str(a.get("announceTime","")),"searchkey":sk,"keyword_group":group_name}
                        all_rows.append(row)
                        group_count[group_name]=group_count.get(group_name,0)+1
                except Exception: pass
            if len(all_rows)>=max_results*3: break
        inv["searchkey_queries_run"]=queries_run
        inv["metadata_rows_collected"]=len(all_rows)
        inv["metadata_rows_after_dedupe"]=len(all_rows)
        inv["keyword_group_breakdown"]=group_count
        inv["rows"]=all_rows
        inv["top_hits"]=[rw for rw in all_rows if rw.get("source_type") in ("investor_relations_record","annual_report","semiannual_report","quarterly_report")][:10]
        inv["status"]="ok" if all_rows else "no_results"
    except Exception as e:
        inv["status"]="error:"+str(e)[:100]
    return r
