#!/usr/bin/env python3
"""Phase 67 pagination inventory report."""
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_cninfo_pagination_query_engine import query_paginated as build
def _md(r):
    inv=r.get("cninfo_pagination_inventory",r)
    lines=["# CNINFO Pagination Inventory",""]
    lines.append("Pages requested: "+str(inv.get("pages_requested",0)))
    lines.append("Pages succeeded: "+str(inv.get("pages_succeeded",0)))
    lines.append("Rows collected: "+str(inv.get("metadata_rows_collected",0)))
    lines.append("After dedupe: "+str(inv.get("metadata_rows_after_dedupe",0)))
    if inv.get("source_type_breakdown"):
        lines.append("");lines.append("Source types:")
        for k,v in inv["source_type_breakdown"].items(): lines.append("- "+k+": "+str(v))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");p.add_argument("--skip-network",action="store_true")
    a=p.parse_args();r=build(a.ticker,skip_network=getattr(a,"skip_network",False))
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
