#!/usr/bin/env python3
"""Phase 67 expanded PDF extraction report."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
J=Path(__file__).resolve().parents[1]/"jobs"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if str(J) not in sys.path: sys.path.insert(0,str(J))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def build(t="300308.SZ",mx=25,skip=False):
    try:
        from run_phase67_expanded_pdf_text_extraction import run_phase67_extraction
        return run_phase67_extraction(t,mx,skip_network=skip,mode="execute" if not skip else "skip")
    except ImportError:
        return {"ticker":t,"phase67_expanded_pdf_text_extraction":{"status":"module_not_found","pdf_text_ok":0,"raw_pdf_saved":False,"ocr_used":False,"rows":[]}}

def _md(r):
    ex=r.get("phase67_expanded_pdf_text_extraction",r)
    lines=["# Phase 67 Expanded PDF Extraction",""]
    lines.append("Selected: "+str(ex.get("pdfs_selected",0)))
    lines.append("Download OK: "+str(ex.get("pdf_download_ok",0)))
    lines.append("Text OK: "+str(ex.get("pdf_text_ok",0)))
    lines.append("IR texts: "+str(ex.get("ir_records_text_ok",0)))
    lines.append("Report texts: "+str(ex.get("reports_text_ok",0)))
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--max-pdfs",type=int,default=25);p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");p.add_argument("--skip-network",action="store_true")
    a=p.parse_args();r=build(a.ticker,a.max_pdfs,skip=getattr(a,"skip_network",False))
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
