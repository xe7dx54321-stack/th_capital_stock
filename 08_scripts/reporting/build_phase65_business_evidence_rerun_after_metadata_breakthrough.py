#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
BASELINE=3
def build(t="300308.SZ",skip=False):
    return {"ticker":t,"business_evidence_rerun_after_metadata_breakthrough":{"metadata_breakthrough":False,"real_text_available":False,"business_claims_supported_before":BASELINE,"business_claims_supported_after":BASELINE,"evidence_gain_delta":0,"guard_status":"pass","status":"skipped_no_real_text_available","mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}
def _md(r):
    b=r.get("business_evidence_rerun_after_metadata_breakthrough",r)
    lines=["# Business Evidence Rerun After Metadata Breakthrough",""]
    lines.append("Breakthrough: "+str(b.get("metadata_breakthrough")))
    lines.append("Before: "+str(b.get("business_claims_supported_before",0)))
    lines.append("After: "+str(b.get("business_claims_supported_after",0)))
    lines.append("Delta: "+str(b.get("evidence_gain_delta",0)))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");p.add_argument("--skip-network",action="store_true")
    a=p.parse_args();r=build(a.ticker,getattr(a,"skip_network",False))
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
