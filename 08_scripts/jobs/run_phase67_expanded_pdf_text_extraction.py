#!/usr/bin/env python3
"""Phase 67 expanded PDF text extraction job."""
import argparse,json,sys,io,urllib.request,hashlib
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
from smr_cninfo_pagination_query_engine import query_paginated
from smr_ir_report_priority_pdf_selector import select_ir_report_pdfs
from smr_business_keyword_hit_scanner import scan_text

def run_phase67_extraction(ticker="300308.SZ",max_pdfs=25,skip_network=False,mode="execute"):
    r={"ticker":ticker,"phase67_expanded_pdf_text_extraction":{"pdfs_selected":0,"pdf_download_ok":0,"pdf_download_failed":0,"pdf_text_ok":0,"pdf_text_failed":0,"texts_written":0,"ir_records_text_ok":0,"reports_text_ok":0,"business_keyword_docs_text_ok":0,"raw_pdf_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False,"rows":[]}}
    ex=r["phase67_expanded_pdf_text_extraction"]
    if mode in ("dry-run","dry_run"): ex["status"]="dry_run";return r
    if skip_network: ex["status"]="skipped_network_disabled";return r
    curated=CURATED_CNINFO_IDENTITIES.get(ticker,{})
    if not curated.get("org_id"): ex["status"]="no_identity";return r
    meta=query_paginated(ticker,max_pages=5,page_size=30,mode="execute")
    rows=meta.get("cninfo_pagination_inventory",{}).get("rows",[])
    sel=select_ir_report_pdfs(rows,max_pdfs)
    selected=sel.get("rows",[])
    ex["pdfs_selected"]=len(selected)
    for s in selected:
        adj=s.get("adjunct_url","")
        sid=s.get("source_id","")
        title=s.get("title","");st=s.get("source_type","")
        row_entry={"source_id":sid,"title":title[:80],"download_status":"pending","text_extraction_status":"pending","text_length":0,"text_hash":"","failure_reason":None,"source_type":st}
        if not adj:
            row_entry["download_status"]="pdf_download_failed";row_entry["failure_reason"]="no_adjunct_url"
            ex["pdf_download_failed"]+=1;ex["rows"].append(row_entry);continue
        full="https://static.cninfo.com.cn/"+adj if not adj.startswith("http") else adj
        try:
            req=urllib.request.Request(full,headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req,timeout=30) as resp: pdf_data=resp.read()
            row_entry["download_status"]="pdf_download_ok"
            try:
                from pypdf import PdfReader;reader=PdfReader(io.BytesIO(pdf_data))
                text="".join((p.extract_text() or "") for p in reader.pages)
                if text and len(text.strip())>100:
                    row_entry["text_extraction_status"]="pdf_text_ok"
                    row_entry["text_length"]=len(text)
                    row_entry["text_hash"]="sha256:"+hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
                    ks=scan_text(text)
                    row_entry["keyword_groups_hit"]=ks.get("keyword_groups",[])
                    ex["pdf_text_ok"]+=1;ex["texts_written"]+=1
                    if st=="investor_relations_record": ex["ir_records_text_ok"]+=1
                    elif st in ("annual_report","semiannual_report","quarterly_report"): ex["reports_text_ok"]+=1
                    elif ks.get("keyword_groups",[]): ex["business_keyword_docs_text_ok"]+=1
                else:
                    row_entry["text_extraction_status"]="pdf_text_too_short";ex["pdf_text_failed"]+=1
            except Exception as e:
                row_entry["text_extraction_status"]="pdf_text_failed";row_entry["failure_reason"]=str(e)[:100];ex["pdf_text_failed"]+=1
            ex["pdf_download_ok"]+=1
        except Exception as e:
            row_entry["download_status"]="pdf_download_failed";row_entry["failure_reason"]=str(e)[:100];ex["pdf_download_failed"]+=1
        ex["rows"].append(row_entry)
    ex["status"]="ok" if ex["pdf_text_ok"]>0 else "degraded_no_text"
    return r

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--max-pdfs",type=int,default=25);p.add_argument("--json",action="store_true")
    a=p.parse_args();mode="execute" if getattr(a,"execute",False) else "dry_run"
    r=run_phase67_extraction(a.ticker,a.max_pdfs,mode=mode)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
