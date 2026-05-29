#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
def build(skip=False):
    return {"summary":{"ticker":"300308.SZ","cninfo_parameter_sets_tested":0,"cninfo_working_sets":0,"cninfo_metadata_sources_found":0,"cninfo_pdf_urls_found":0,"pdf_text_ok":0,"szse_working_endpoints":0,"best_available_path":"pending_network_verification","metadata_breakthrough":False,"real_text_available":False,"business_evidence_delta":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def _md(r):
    s=r.get("summary",r)
    lines=["# Phase 65 Disclosure Metadata Breakthrough Dashboard",""]
    lines.append("Breakthrough: "+str(s.get("metadata_breakthrough")))
    lines.append("Best Path: "+str(s.get("best_available_path")))
    lines.append("Evidence Delta: "+str(s.get("business_evidence_delta",0)))
    lines.append("Mock/Fixture: "+str(s.get("mock_used"))+"/"+str(s.get("fixture_used")))
    lines.append("Raw/OCR: "+str(s.get("raw_saved"))+"/"+str(s.get("ocr_used")))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");p.add_argument("--skip-network",action="store_true")
    a=p.parse_args();r=build(getattr(a,"skip_network",False))
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
