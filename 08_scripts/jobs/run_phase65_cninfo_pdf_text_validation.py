#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true");p.add_argument("--max-pdfs",type=int,default=3);p.add_argument("--json",action="store_true")
    a=p.parse_args()
    mode="dry-run" if getattr(a,"dry_run",False) else "execute"
    if mode=="dry-run":
        r={"ticker":a.ticker,"cninfo_pdf_text_validation":{"mode":"dry_run","max_pdfs":a.max_pdfs,"network_attempted":False,"raw_pdf_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False}}
    else:
        r={"ticker":a.ticker,"cninfo_pdf_text_validation":{"mode":"execute","pdfs_checked":0,"pdf_download_ok":0,"pdf_download_failed":0,"pdf_text_ok":0,"pdf_text_failed":0,"raw_pdf_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False,"rows":[],"status":"requires_network_environment"}}
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
