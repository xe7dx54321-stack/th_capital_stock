#!/usr/bin/env python3
import argparse,json,sys,urllib.request,urllib.parse
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
CNINFO_API="https://www.cninfo.com.cn/new/hisAnnouncement/query"
HEADERS={"User-Agent":"Mozilla/5.0","Accept":"application/json","Referer":"https://www.cninfo.com.cn/","Content-Type":"application/x-www-form-urlencoded"}
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--skip-network",action="store_true");p.add_argument("--max-sources",type=int,default=10);p.add_argument("--json",action="store_true")
    a=p.parse_args();t=a.ticker;mode="dry-run" if getattr(a,"dry_run",False) else "execute";skip=getattr(a,"skip_network",False);mx=a.max_sources
    curated=CURATED_CNINFO_IDENTITIES.get(t,{});org_id=curated.get("org_id","");code=curated.get("security_code",t.split(".")[0]);stock_param=code+","+org_id if org_id else code
    r={"ticker":t,"cninfo_real_metadata_inventory":{"identity_map_used":bool(org_id),"stock_param":stock_param,"metadata_sources_found":0,"metadata_sources_written":0,"source_types":{},"max_sources":mx,"raw_content_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False,"rows":[]}}
    inv=r["cninfo_real_metadata_inventory"]
    if mode=="dry-run": inv["status"]="dry_run";print(json.dumps(r,ensure_ascii=False,indent=2));return
    if skip: inv["status"]="skipped_network_disabled";print(json.dumps(r,ensure_ascii=False,indent=2));return
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
            inv["rows"].append({"source_id":"cninfo_"+code+"_"+str(a.get("announcementId","")),"title":ttl,"publish_date":str(a.get("announceTime","")),"source_type":st,"pdf_url_available":bool(adj),"allowed_usage":"metadata_until_text_extracted"})
        inv["metadata_sources_written"]=len(inv["rows"]);inv["source_types"]=types;inv["status"]="ok" if inv["rows"] else "zero_result"
    except Exception as e: inv["status"]="error";inv["failure_reason"]=str(e)[:100]
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
