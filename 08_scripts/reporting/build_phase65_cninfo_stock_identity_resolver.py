#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_cninfo_stock_identity_resolver import resolve_cninfo_identity

def build(t="300308.SZ", skip=False): return resolve_cninfo_identity(t, skip)

def _md(r):
    res = r.get("cninfo_stock_identity_resolver", r)
    lines = ["# CNINFO Stock Identity Resolver: " + r.get("ticker",""), ""]
    lines.append("Network Attempted: " + str(res.get("network_attempted")))
    lines.append("Parameter Sets Tested: " + str(res.get("parameter_sets_tested", 0)))
    lines.append("Working Sets: " + str(len(res.get("working_parameter_sets", []))))
    if res.get("best_parameter_set"):
        lines.append("Best Set: " + json.dumps(res.get("best_parameter_set"), ensure_ascii=False))
    if res.get("likely_root_cause"):
        lines.append("Root Cause: " + res.get("likely_root_cause"))
    lines.append("Mock: " + str(res.get("mock_used", False)))
    lines.append("Fixture: " + str(res.get("fixture_used", False)))
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ticker",default="300308.SZ")
    p.add_argument("--json",action="store_true")
    p.add_argument("--markdown",action="store_true")
    p.add_argument("--skip-network",action="store_true")
    a=p.parse_args()
    r=build(a.ticker, getattr(a,"skip_network",False))
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
