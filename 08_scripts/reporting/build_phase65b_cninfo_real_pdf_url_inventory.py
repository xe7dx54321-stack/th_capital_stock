#!/usr/bin/env python3
import argparse,json,sys,urllib.request,urllib.parse
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
from smr_cninfo_pdf_url_extractor import extract_pdf_urls_from_metadata
CNINFO_API="https://www.cninfo.com.cn/new/hisAnnouncement/query"
HEADERS={"User-Agent":"Mozilla/5.0","Accept":"application/json","Referer":"https://www.cninfo.com.cn/","Content-Type":"application/x-www-form-urlencoded"}
def build(t="300308.SZ",mx=10,skip=False):
    curated=CURATED_CNINFO_IDENTITIES.get(t,{});org_id=curated.get("org_id","");code=curated.get("security_code",t.split(".")[0])
    stock_param=code+","+org_id if org_id else code
    r={"ticker":t,"cninfo_real_pdf_url_inventory":{"metadata_sources_checked":0,"pdf_urls_found":0,"pdf_urls_valid_format":0,"missing_pdf_url":0,"rows":[],"raw_pdf_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False}}
    inv=r["cninfo_real_pdf_url_inventory"]
    if skip: inv["status"]="skipped_network_disabled";return r
    try:
        params={"pageNum":1,"pageSize":min(mx,30),"stock":stock_param,"plate":curated.get("plate","sz"),"column":curated.get("column","szse"),"tabName":"fulltext","searchkey":"","secid":"","category":"","trade":"","seDate":""}
        data=urllib.parse.urlencode(params).encode()
        req=urllib.request.Request(CNINFO_API,data=data,headers=dict(HEADERS))
        with urllib.request.urlopen(req,timeout=20) as resp:
            body=json.loads(resp.read().decode("utf-8",errors="replace"))
        anns=body.get("announcements",[]);inv["metadata_sources_checked"]=len(anns)
        rows=[{"source_id":str(a.get("announcementId","")),"title":a.get("announcementTitle",""),"publish_date":str(a.get("announceTime","")),"adjunctUrl":a.get("adjunctUrl","")} for a in anns[:mx]]
        extracted=extract_pdf_urls_from_metadata(rows)
        inv["rows"]=extracted
        inv["pdf_urls_found"]=sum(1 for rw in extracted if rw.get("url_status")=="valid_format")
        inv["pdf_urls_valid_format"]=inv["pdf_urls_found"]
        inv["missing_pdf_url"]=sum(1 for rw in extracted if rw.get("url_status")=="missing_or_invalid")
        inv["status"]="ok"
    except Exception as e: inv["status"]="error";inv["failure_reason"]=str(e)[:100]
    return r
def _md(r):
    inv=r.get("cninfo_real_pdf_url_inventory",r)
    lines=["# CNINFO Real PDF URL Inventory",""]
    lines.append("Sources: "+str(inv.get("metadata_sources_checked",0)))
    lines.append("PDF URLs: "+str(inv.get("pdf_urls_found",0)))
    lines.append("Missing: "+str(inv.get("missing_pdf_url",0)))
    for rw in inv.get("rows",[])[:5]:
        lines.append("- "+str(rw.get("title",""))[:50]+": "+rw.get("url_status",""))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");p.add_argument("--skip-network",action="store_true")
    a=p.parse_args();r=build(a.ticker,skip=getattr(a,"skip_network",False))
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
