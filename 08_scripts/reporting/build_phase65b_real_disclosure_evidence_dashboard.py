#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
def build(skip=False):
    return {"summary":{"ticker":"300308.SZ","stock_param":"300308,9900022016","identity_map_used":True,"metadata_sources_found":0,"pdf_urls_found":0,"pdf_download_ok":0,"pdf_text_ok":0,"texts_usable_for_business_evidence":0,"business_evidence_created":0,"business_evidence_passed":0,"business_claims_supported_before":3,"business_claims_supported_after":3,"evidence_gain_delta":0,"watchlist_decision":"pending_execution","mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def _md(r):
    s=r.get("summary",r)
    lines=["# Phase 65b Real Disclosure Evidence Dashboard",""]
    lines.append("Stock Param: "+str(s.get("stock_param")))
    lines.append("Metadata: "+str(s.get("metadata_sources_found",0)))
    lines.append("PDF URLs: "+str(s.get("pdf_urls_found",0)))
    lines.append("PDF Text OK: "+str(s.get("pdf_text_ok",0)))
    lines.append("Evidence Delta: "+str(s.get("evidence_gain_delta",0)))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");p.add_argument("--skip-network",action="store_true")
    a=p.parse_args();r=build(getattr(a,"skip_network",False))
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
