#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_szse_disclosure_connector import fetch_szse_disclosure

def build(ticker="300308.SZ"):
    return fetch_szse_disclosure(ticker, max_sources=15, mode="execute", skip_network=False)

def _md(result):
    inv = result.get("szse_disclosure_inventory", result)
    lines = [f"# SZSE Disclosure Inventory: {result.get('ticker', 'N/A')}", ""]
    lines.append(f"Network Attempted: {inv.get('network_attempted', False)}")
    lines.append(f"Mode: {inv.get('mode', 'N/A')}")
    lines.append(f"SZSE Reachable: {inv.get('szse_reachable', False)}")
    lines.append(f"Status: {inv.get('status', 'N/A')}")
    lines.append(f"Metadata Sources Found: {inv.get('metadata_sources_found', 0)}")
    lines.append(f"PDF URLs Found: {inv.get('pdf_urls_found', 0)}")
    lines.append(f"Text URLs Found: {inv.get('text_urls_found', 0)}")
    lines.append(f"Raw Content Saved: {inv.get('raw_content_saved', False)}")
    lines.append(f"OCR Used: {inv.get('ocr_used', False)}")
    if inv.get("failure_reason"):
        lines.append(f"Failure Reason: {inv['failure_reason']}")
    lines.append("")
    if inv.get("source_types"):
        lines.append("## Source Types")
        for k, v in inv["source_types"].items():
            lines.append(f"- {k}: {v}")
        lines.append("")
    if inv.get("rows"):
        lines.append("## Sources")
        for row in inv["rows"][:15]:
            lines.append(f"- {row.get('source_id', '')}: {row.get('title', '')} ({row.get('source_type', '')})")
        if len(inv.get("rows", [])) > 15:
            lines.append(f"- ... and {len(inv['rows']) - 15} more")
        lines.append("")
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ticker",default="300308.SZ")
    p.add_argument("--json",action="store_true")
    p.add_argument("--markdown",action="store_true")
    args=p.parse_args()
    result=build(args.ticker)
    if args.json: print(json.dumps(result,ensure_ascii=False,indent=2))
    elif args.markdown: print(_md(result))
    else: print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
