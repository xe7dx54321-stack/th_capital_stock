#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_cninfo_targeted_metadata_harvester import harvest_targeted_metadata as build
def _md(r):
    inv=r.get("cninfo_targeted_metadata_inventory",r)
    lines=["# CNINFO Targeted Metadata Inventory",""]
    lines.append("Identity: "+str(inv.get("identity_map_used")))
    lines.append("Total Found: "+str(inv.get("metadata_sources_found",0)))
    lines.append("Selected: "+str(inv.get("targeted_metadata_selected",0)))
    if inv.get("category_breakdown"):
        for k,v in inv["category_breakdown"].items(): lines.append("- "+k+": "+str(v))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");p.add_argument("--skip-network",action="store_true")
    a=p.parse_args();r=build(a.ticker,skip_network=getattr(a,"skip_network",False))
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
