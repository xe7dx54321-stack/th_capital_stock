#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase74_irm_html_qa_parser import parse_irm_html
def run(mode="execute",tickers=None):
 if tickers is None:tickers=["300308.SZ","688041.SH","300394.SZ"]
 sn=mode=="skip_network"
 rows=[parse_irm_html(t,skip_network=sn) for t in tickers]
 qa=sum(r.get("qa_items_found",0) for r in rows)
 usable=sum(r.get("qa_text_usable",0) for r in rows)
 return{"phase74_irm_html_qa_parse":{"mode":mode,"tickers_checked":len(tickers),"html_pages_fetched":sum(1 for r in rows if r.get("html_fetched")),"qa_items_found":qa,"qa_text_usable":usable,"rows":rows,"raw_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False}}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true")
 p.add_argument("--skip-network",action="store_true");p.add_argument("--json",action="store_true")
 a=p.parse_args()
 mode="skip_network" if a.skip_network else ("dry_run" if getattr(a,"dry_run") else "execute")
 r=run(mode)
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
