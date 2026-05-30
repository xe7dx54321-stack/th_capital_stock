#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase74_sse_html_disclosure_parser import parse_sse_html
def run(mode="execute",tickers=None):
 if tickers is None:tickers=["688041.SH"]
 sn=mode=="skip_network"
 rows=[parse_sse_html(t,skip_network=sn) for t in tickers]
 r0=rows[0] if rows else{}
 return{"phase74_sse_html_disclosure_parse":{"mode":mode,"ticker":"688041.SH","html_pages_fetched":r0.get("html_pages_fetched",0),"announcement_links_found":r0.get("announcement_links_found",0),"pdf_links_found":r0.get("pdf_links_found",0),"text_pages_found":r0.get("text_pages_found",0),"rows":r0.get("rows",[]),"raw_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False}}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true")
 p.add_argument("--skip-network",action="store_true");p.add_argument("--json",action="store_true")
 a=p.parse_args()
 mode="skip_network" if a.skip_network else ("dry_run" if getattr(a,"dry_run") else "execute")
 r=run(mode)
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
