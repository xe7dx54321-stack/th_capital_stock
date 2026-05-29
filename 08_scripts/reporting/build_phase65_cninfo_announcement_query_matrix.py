#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_cninfo_announcement_query_matrix import run_announcement_query_matrix as build
def _md(r):
    m=r.get("cninfo_announcement_query_matrix",r)
    lines=["# CNINFO Announcement Query Matrix",""]
    lines.append("Sets Tested: "+str(m.get("parameter_sets_tested",0)))
    lines.append("Successful: "+str(m.get("successful_sets",0)))
    lines.append("Zero Result: "+str(m.get("zero_result_sets",0)))
    lines.append("Error: "+str(m.get("error_sets",0)))
    if m.get("best_set"):
        lines.append("Best: "+json.dumps(m["best_set"],ensure_ascii=False))
    if m.get("top_failure_reasons"):
        lines.append("Top Failures: "+str(m["top_failure_reasons"]))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser(); p.add_argument("--ticker",default="300308.SZ"); p.add_argument("--json",action="store_true"); p.add_argument("--markdown",action="store_true"); p.add_argument("--skip-network",action="store_true")
    a=p.parse_args(); r=build(a.ticker,getattr(a,"skip_network",False))
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
