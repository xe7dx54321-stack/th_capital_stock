#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_cninfo_targeted_disclosure_category_planner import load_category_plan,get_max_metadata_default
def build(t="300308.SZ"):
    plan=load_category_plan();plan["ticker"]=t;plan["max_metadata_default"]=get_max_metadata_default()
    return plan
def _md(r):
    cats=r.get("priority_categories",[])
    lines=["# CNINFO Targeted Disclosure Category Plan",""]
    for c in cats:
        lines.append("## "+c["category_key"]+" ("+c["priority"]+")")
        lines.append("- Max sources: "+str(c.get("max_sources","")))
        lines.append("- Reason: "+c.get("reason",""))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
