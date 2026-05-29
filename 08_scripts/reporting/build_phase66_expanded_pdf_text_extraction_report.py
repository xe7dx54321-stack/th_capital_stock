#!/usr/bin/env python3
"""Phase 66 expanded PDF text extraction report."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
J=Path(__file__).resolve().parents[1]/"jobs"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if str(J) not in sys.path: sys.path.insert(0,str(J))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def build(t="300308.SZ",mx=15,skip=False):
    try:
        from run_phase66_expanded_pdf_text_extraction import run_expanded_extraction
        return run_expanded_extraction(t,mx,skip_network=skip,mode="execute" if not skip else "skip")
    except ImportError:
        return {"ticker":t,"expanded_pdf_text_extraction":{"status":"job_module_not_found","pdfs_selected":0,"pdf_text_ok":0,"pdf_download_ok":0,"raw_pdf_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False,"rows":[]}}

def _md(r):
    ex=r.get("expanded_pdf_text_extraction",r)
    lines=["# Expanded PDF Text Extraction",""]
    lines.append("Selected: "+str(ex.get("pdfs_selected",0)))
    lines.append("Download OK: "+str(ex.get("pdf_download_ok",0)))
    lines.append("Failed: "+str(ex.get("pdf_download_failed",0)))
    lines.append("Text OK: "+str(ex.get("pdf_text_ok",0)))
    lines.append("Text Failed: "+str(ex.get("pdf_text_failed",0)))
    for row in ex.get("rows",[])[:5]:
        lines.append("- "+str(row.get("title",""))[:50]+" ["+str(row.get("text_extraction_status",""))+"]")
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--max-pdfs",type=int,default=15);p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");p.add_argument("--skip-network",action="store_true")
    a=p.parse_args();r=build(a.ticker,a.max_pdfs,skip=getattr(a,"skip_network",False))
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
