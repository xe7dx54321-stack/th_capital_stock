#!/usr/bin/env python3
import argparse,json,sys,io,urllib.request,urllib.parse
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
CNINFO_API="https://www.cninfo.com.cn/new/hisAnnouncement/query"
HEADERS={"User-Agent":"Mozilla/5.0","Accept":"application/json","Referer":"https://www.cninfo.com.cn/","Content-Type":"application/x-www-form-urlencoded"}
def _try_pdf(url):
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"});
        with urllib.request.urlopen(req,timeout=20) as resp: pdf_data=resp.read()
        try:
            from pypdf import PdfReader;reader=PdfReader(io.BytesIO(pdf_data))
            text="".join((p.extract_text() or "") for p in reader.pages)
            return {"status":"pdf_text_ok","text_length":len(text),"pages":len(reader.pages),"text":text}
        except ImportError: return {"status":"pdf_text_failed","failure_reason":"pypdf_not_available"}
    except Exception as e: return {"status":"pdf_download_failed","failure_reason":str(e)[:100]}
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--max-pdfs",type=int,default=5);p.add_argument("--json",action="store_true")
    a=p.parse_args();t=a.ticker;mode="dry-run" if getattr(a,"dry_run",False) else "execute";mx=a.max_pdfs
    curated=CURATED_CNINFO_IDENTITIES.get(t,{});org_id=curated.get("org_id","");code=curated.get("security_code",t.split(".")[0])
    stock_param=code+","+org_id if org_id else code
    r={"ticker":t,"cninfo_real_pdf_text_extraction":{"pdfs_checked":0,"pdf_download_ok":0,"pdf_download_failed":0,"pdf_text_ok":0,"pdf_text_failed":0,"texts_written":0,"raw_pdf_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False,"rows":[]}}
    e=r["cninfo_real_pdf_text_extraction"]
    if mode=="dry-run": e["status"]="dry_run";e["max_pdfs"]=mx;print(json.dumps(r,ensure_ascii=False,indent=2));return
    try:
        params={"pageNum":1,"pageSize":min(mx,10),"stock":stock_param,"plate":curated.get("plate","sz"),"column":curated.get("column","szse"),"tabName":"fulltext","searchkey":"","secid":"","category":"","trade":"","seDate":""}
        data=urllib.parse.urlencode(params).encode()
        req=urllib.request.Request(CNINFO_API,data=data,headers=dict(HEADERS))
        with urllib.request.urlopen(req,timeout=20) as resp:
            body=json.loads(resp.read().decode("utf-8",errors="replace"))
        for ann in body.get("announcements",[])[:mx]:
            rel=ann.get("adjunctUrl","");e["pdfs_checked"]+=1
            if not rel: e["rows"].append({"title":(ann.get("announcementTitle","") or "")[:60],"download_status":"no_pdf_url","text_extraction_status":"skipped"});e["pdf_download_failed"]+=1;continue
            full="https://static.cninfo.com.cn/"+rel if not rel.startswith("http") else rel
            pr=_try_pdf(full);pr["title"]=(ann.get("announcementTitle","") or "")[:60]
            if pr["status"]=="pdf_text_ok": e["pdf_download_ok"]+=1;e["pdf_text_ok"]+=1;e["texts_written"]+=1
            elif pr["status"]=="pdf_text_failed": e["pdf_download_ok"]+=1;e["pdf_text_failed"]+=1
            else: e["pdf_download_failed"]+=1
            row={"title":pr.get("title",""),"download_status":"pdf_download_ok" if pr["status"]!="pdf_download_failed" else "pdf_download_failed","text_extraction_status":pr["status"],"text_length":pr.get("text_length",0),"failure_reason":pr.get("failure_reason")}
            e["rows"].append(row)
        e["status"]="ok" if e["pdf_text_ok"]>0 else "degraded_no_text"
    except Exception as ex: e["status"]="error";e["failure_reason"]=str(ex)[:100]
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
