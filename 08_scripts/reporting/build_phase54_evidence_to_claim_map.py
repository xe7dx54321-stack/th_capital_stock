#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_evidence_to_claim_mapper import build_evidence_map
def build(conn,ticker): return build_evidence_map(ticker)
def _md(p): m=p.get("evidence_to_claim_map",{}); lines=["# Evidence-to-Claim Map","","supported: "+str(m.get("claims_supported",""))+", unconfirmed: "+str(m.get("claims_unconfirmed",""))]; [lines.append("- "+r.get("claim_readable","")+": "+r.get("evidence_strength","")) for r in m.get("rows",[])]; return "\n".join(lines)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ticker",default="300308.SZ")
    p.add_argument("--json",action="store_true")
    p.add_argument("--markdown",action="store_true")
    args=p.parse_args()
    r=build(None,args.ticker)
    if args.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
