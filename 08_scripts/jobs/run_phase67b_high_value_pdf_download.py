#!/usr/bin/env python3
"""Phase 67b high-value PDF download + extraction job."""
import argparse,json,sys,io,urllib.request,hashlib
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_phase67_high_value_pdf_pool_loader import load_high_value_pool
from smr_business_keyword_hit_scanner import scan_text

def download_and_extract(ticker="300308.SZ",max_pdfs=25,skip_network=False,mode="execute"):
    r={"ticker":ticker,"high_value_pdf_download":{"pdfs_selected":0,"pdf_download_ok":0,"pdf_download_failed":0,"raw_pdf_saved":False,"rows":[]}}
    d=r["high_value_pdf_download"]
    if mode in ("dry-run","dry_run"): d["status"]="dry_run";return r
    if skip_network: d["status"]="skipped_network_disabled";return r
    try:
        pool=load_high_value_pool(ticker,max_pages=5,max_pdfs=max_pdfs)
        rows=pool.get("phase67b_high_value_pdf_pool",{}).get("rows",[])
        d["pdfs_selected"]=len(rows)
        for rw in rows:
            adj=rw.get("adjunct_url","");sid=rw.get("source_id","");title=rw.get("title","");st=rw.get("source_type","")
            entry={"source_id":sid,"source_type":st,"title":title[:80],"download_status":"pending","text_extraction_status":"pending","text_length":0,"text_hash":"","failure_reason":None}
            if not adj: entry["download_status"]="pdf_download_failed";entry["failure_reason"]="no_adjunct_url";d["pdf_download_failed"]+=1;d["rows"].append(entry);continue
            full="https://static.cninfo.com.cn/"+adj if not adj.startswith("http") else adj
            try:
                req=urllib.request.Request(full,headers={"User-Agent":"Mozilla/5.0"})
                with urllib.request.urlopen(req,timeout=30) as resp: pdf_data=resp.read()
                entry["download_status"]="pdf_download_ok";d["pdf_download_ok"]+=1
                try:
                    from pypdf import PdfReader;reader=PdfReader(io.BytesIO(pdf_data))
                    text="".join((p.extract_text() or "") for p in reader.pages)
                    if text and len(text.strip())>100:
                        entry["text_extraction_status"]="pdf_text_ok";entry["text_length"]=len(text)
                        entry["text_hash"]="sha256:"+hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
                        ks=scan_text(text);entry["keyword_groups_hit"]=ks.get("keyword_groups",[])
                    else: entry["text_extraction_status"]="pdf_text_too_short";entry["failure_reason"]="text under 100 chars"
                except Exception as e: entry["text_extraction_status"]="pdf_text_failed";entry["failure_reason"]=str(e)[:100]
            except Exception as e: entry["download_status"]="pdf_download_failed";entry["failure_reason"]=str(e)[:100];d["pdf_download_failed"]+=1
            d["rows"].append(entry)
        d["status"]="ok" if d["pdf_download_ok"]>0 else "degraded"
    except Exception as e: d["status"]="error:"+str(e)[:80]
    return r

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--max-pdfs",type=int,default=25);p.add_argument("--json",action="store_true")
    a=p.parse_args();mode="execute" if getattr(a,"execute",False) else "dry_run"
    r=download_and_extract(a.ticker,a.max_pdfs,mode=mode)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
