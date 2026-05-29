#!/usr/bin/env python3
"""Phase 67 category+searchkey matrix report."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_cninfo_category_searchkey_matrix import run_matrix as build
def _md(r):
    mx=r.get("category_searchkey_matrix",r)
    lines=["# Category + Searchkey Matrix",""]
    lines.append("Sets tested: "+str(mx.get("parameter_sets_tested",0)))
    lines.append("Successful: "+str(mx.get("successful_sets",0)))
    lines.append("Zero results: "+str(mx.get("zero_result_sets",0)))
    lines.append("Errors: "+str(mx.get("error_sets",0)))
    for bs in mx.get("best_sets",[])[:5]:
        lines.append("- "+bs["category"]+" + "+bs["searchkey"]+" = "+str(bs["results_count"])+" results")
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");p.add_argument("--skip-network",action="store_true")
    a=p.parse_args();r=build(a.ticker,skip_network=getattr(a,"skip_network",False))
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
