#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_szse_endpoint_explorer import explore_szse_endpoints as build
def _md(r):
    e=r.get("szse_endpoint_explorer",r)
    lines=["# SZSE Endpoint Explorer",""]
    lines.append("Tested: "+str(e.get("endpoints_tested",0)))
    lines.append("Working: "+str(len(e.get("working_endpoints",[]))))
    lines.append("Failed: "+str(len(e.get("failed_endpoints",[]))))
    if e.get("best_endpoint"): lines.append("Best: "+e["best_endpoint"])
    for f in e.get("failed_endpoints",[])[:5]:
        lines.append("- "+f.get("endpoint","")+": "+str(f.get("http_status",""))+" "+str(f.get("failure_reason","")))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");p.add_argument("--skip-network",action="store_true")
    a=p.parse_args();r=build(a.ticker,getattr(a,"skip_network",False))
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
