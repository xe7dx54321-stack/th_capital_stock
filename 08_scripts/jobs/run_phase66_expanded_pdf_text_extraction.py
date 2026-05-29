#!/usr/bin/env python3
"""Phase 66 expanded PDF text extraction job."""
import argparse,json,sys,io,urllib.request,hashlib
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
from smr_priority_pdf_selector import select_priority_pdfs
from smr_cninfo_targeted_metadata_harvester import harvest_targeted_metadata
from smr_business_keyword_hit_scanner import scan_text

def run_expanded_extraction(ticker="300308.SZ",max_pdfs=15,skip_network=False,mode="execute"):
    r={"ticker":ticker,"expanded_pdf_text_extraction":{"pdfs_selected":0,"pdf_download_ok":0,"pdf_download_failed":0,"pdf_text_ok":0,"pdf_text_failed":0,"texts_written":0,"raw_pdf_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False,"rows":[]}}
    ex=r["expanded_pdf_text_extraction"]
    if mode in ("dry-run","dry_run"): ex["status"]="dry_run";return r
    if skip_network: ex["status"]="skipped_network_disabled";return r
    curated=CURATED_CNINFO_IDENTITIES.get(ticker,{})
    if not curated.get("org_id"): ex["status"]="no_identity";return r
    meta=harvest_targeted_metadata(ticker,max_metadata=50)
    rows=meta.get("cninfo_targeted_metadata_inventory",{}).get("rows",[])
    sel=select_priority_pdfs(rows,max_pdfs)
    selected=sel.get("rows",[])
    ex["pdfs_selected"]=len(selected)
    CNINFO_API="https://www.cninfo.com.cn/new/hisAnnouncement/query"
    HEADERS={"User-Agent":"Mozilla/5.0","Accept":"application/json","Referer":"https://www.cninfo.com.cn/","Content-Type":"application/x-www-form-urlencoded"}
    urls=[]
    for s in selected:
        sid=s.get("source_id","")
        for rw in rows:
            if rw.get("source_id")==sid:
                adj=rw.get("adjunct_url","")
                if adj:
                    full="https://static.cninfo.com.cn/"+adj if not adj.startswith("http") else adj
                    urls.append({"source_id":sid,"title":rw.get("title",""),"pdf_url":full,"source_type":rw.get("source_type","")})
                break
    import urllib.parse as up
    for u in urls[:max_pdfs]:
        row_entry={"source_id":u["source_id"],"title":u["title"][:80],"download_status":"pending","text_extraction_status":"pending","text_length":0,"text_hash":"","allowed_usage":"","failure_reason":None}
        try:
            req=urllib.request.Request(u["pdf_url"],headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req,timeout=30) as resp: pdf_data=resp.read()
            row_entry["download_status"]="pdf_download_ok"
            try:
                from pypdf import PdfReader;reader=PdfReader(io.BytesIO(pdf_data))
                text="".join((p.extract_text() or "") for p in reader.pages)
                if text and len(text.strip())>100:
                    row_entry["text_extraction_status"]="pdf_text_ok"
                    row_entry["text_length"]=len(text)
                    row_entry["text_hash"]="sha256:"+hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
                    row_entry["allowed_usage"]="real_disclosure_text"
                    ks=scan_text(text)
                    row_entry["keyword_groups_hit"]=ks.get("keyword_groups",[])
                    ex["texts_written"]+=1;ex["pdf_text_ok"]+=1
                else:
                    row_entry["text_extraction_status"]="pdf_text_too_short"
                    row_entry["failure_reason"]="extracted text under 100 chars"
                    ex["pdf_text_failed"]+=1
            except ImportError:
                row_entry["text_extraction_status"]="pdf_text_failed"
                row_entry["failure_reason"]="pypdf not available"
                ex["pdf_text_failed"]+=1
            except Exception as e:
                row_entry["text_extraction_status"]="pdf_text_failed"
                row_entry["failure_reason"]=str(e)[:100]
                ex["pdf_text_failed"]+=1
            ex["pdf_download_ok"]+=1
        except Exception as e:
            row_entry["download_status"]="pdf_download_failed"
            row_entry["failure_reason"]=str(e)[:100]
            ex["pdf_download_failed"]+=1
        ex["rows"].append(row_entry)
    ex["status"]="ok" if ex["pdf_text_ok"]>0 else "degraded_no_successful_text"
    return r

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ticker",default="300308.SZ")
    p.add_argument("--dry-run",action="store_true")
    p.add_argument("--execute",action="store_true")
    p.add_argument("--max-pdfs",type=int,default=15)
    p.add_argument("--json",action="store_true")
    a=p.parse_args()
    mode="execute" if getattr(a,"execute",False) else "dry_run"
    skip=getattr(a,"skip_network",False)
    r=run_expanded_extraction(a.ticker,a.max_pdfs,skip_network=skip,mode=mode)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
