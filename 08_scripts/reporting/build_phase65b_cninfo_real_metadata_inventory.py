#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
# Reuse the job module logic
import urllib.request,urllib.parse
from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
CNINFO_API="https://www.cninfo.com.cn/new/hisAnnouncement/query"
HEADERS={"User-Agent":"Mozilla/5.0","Accept":"application/json","Referer":"https://www.cninfo.com.cn/","Content-Type":"application/x-www-form-urlencoded"}
def build(t="300308.SZ",mx=10,skip=False):
    curated=CURATED_CNINFO_IDENTITIES.get(t,{});org_id=curated.get("org_id","");code=curated.get("security_code",t.split(".")[0]);stock_param=code+","+org_id if org_id else code
    r={"ticker":t,"cninfo_real_metadata_inventory":{"identity_map_used":bool(org_id),"stock_param":stock_param,"metadata_sources_found":0,"metadata_sources_written":0,"source_types":{},"max_sources":mx,"raw_content_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False,"rows":[]}}
    inv=r["cninfo_real_metadata_inventory"]
    if skip: inv["status"]="skipped_network_disabled";return r
    try:
        params={"pageNum":1,"pageSize":min(mx,30),"stock":stock_param,"plate":curated.get("plate","sz"),"column":curated.get("column","szse"),"tabName":"fulltext","searchkey":"","secid":"","category":"","trade":"","seDate":""}
        data=urllib.parse.urlencode(params).encode()
        req=urllib.request.Request(CNINFO_API,data=data,headers=dict(HEADERS))
        with urllib.request.urlopen(req,timeout=20) as resp:
            body=json.loads(resp.read().decode("utf-8",errors="replace"))
        anns=body.get("announcements",[]);inv["metadata_sources_found"]=body.get("totalAnnouncement",0)
        types={}
        for a in anns[:mx]:
            ttl=(a.get("announcementTitle","") or "");adj=a.get("adjunctUrl","")
            if "年度报告" in ttl: st="annual_report"
            elif "半年度" in ttl: st="semiannual_report"
            elif "季度报告" in ttl or "季报" in ttl: st="quarterly_report"
            elif "投资者关系" in ttl or "调研" in ttl: st="investor_relations_record"
            else: st="announcement"
            types[st]=types.get(st,0)+1
            inv["rows"].append({"source_id":"cninfo_"+code+"_"+str(a.get("announcementId","")),"title":ttl,"source_type":st,"pdf_url_available":bool(adj)})
        inv["metadata_sources_written"]=len(inv["rows"]);inv["source_types"]=types;inv["status"]="ok"
    except Exception as e: inv["status"]="error";inv["failure_reason"]=str(e)[:100]
    return r
def _md(r):
    inv=r.get("cninfo_real_metadata_inventory",r)
    lines=["# CNINFO Real Metadata Inventory",""]
    lines.append("Identity Used: "+str(inv.get("identity_map_used")))
    lines.append("Stock Param: "+str(inv.get("stock_param","")))
    lines.append("Total: "+str(inv.get("metadata_sources_found",0)))
    lines.append("Written: "+str(inv.get("metadata_sources_written",0)))
    if inv.get("source_types"):
        for k,v in inv["source_types"].items(): lines.append("- "+k+": "+str(v))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");p.add_argument("--skip-network",action="store_true")
    a=p.parse_args();r=build(a.ticker,skip=getattr(a,"skip_network",False))
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
