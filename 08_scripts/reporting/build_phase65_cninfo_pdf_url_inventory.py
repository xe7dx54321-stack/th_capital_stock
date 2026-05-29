#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_cninfo_pdf_url_extractor import build_pdf_url_inventory as build
def _md(r):
    inv=r.get("cninfo_pdf_url_inventory",r)
    lines=["# CNINFO PDF URL Inventory",""]
    lines.append("Sources: "+str(inv.get("metadata_sources_checked",0)))
    lines.append("PDF URLs: "+str(inv.get("pdf_urls_found",0)))
    lines.append("Raw Saved: "+str(inv.get("raw_pdf_saved",False)))
    if inv.get("rows"):
        for row in inv["rows"][:10]:
            lines.append("- "+str(row.get("title",""))[:60]+": "+row.get("url_status",""))
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");p.add_argument("--ticker",default="300308.SZ")
    a=p.parse_args();r=build(a.ticker)
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
