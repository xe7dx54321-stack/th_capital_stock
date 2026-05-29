#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
def build(t="300308.SZ"):
    return {"ticker":t,"cninfo_real_pdf_text_extraction":{"pdfs_checked":0,"pdf_download_ok":0,"pdf_download_failed":0,"pdf_text_ok":0,"pdf_text_failed":0,"raw_pdf_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False,"status":"requires_network_execution"}}
def _md(r):
    e=r.get("cninfo_real_pdf_text_extraction",r)
    lines=["# CNINFO Real PDF Text Extraction",""]
    lines.append("PDFs Checked: "+str(e.get("pdfs_checked",0)))
    lines.append("Download OK: "+str(e.get("pdf_download_ok",0)))
    lines.append("Text OK: "+str(e.get("pdf_text_ok",0)))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
