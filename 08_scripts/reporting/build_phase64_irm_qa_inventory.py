#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_irm_interactive_qa_connector import fetch_irm_qa

def build(ticker="300308.SZ"):
    return fetch_irm_qa(ticker, max_sources=10, mode="execute", skip_network=False)

def _md(result):
    inv = result.get("irm_qa_inventory", result)
    lines = [f"# IRM QA Inventory: {result.get('ticker', 'N/A')}", ""]
    lines.append(f"Network Attempted: {inv.get('network_attempted', False)}")
    lines.append(f"IRM Reachable: {inv.get('irm_reachable', False)}")
    lines.append(f"API JSON Available: {inv.get('api_json_available', False)}")
    lines.append(f"HTML Parse Available: {inv.get('html_parse_available', False)}")
    lines.append(f"QA Items Found: {inv.get('qa_items_found', 0)}")
    lines.append(f"QA Items Usable: {inv.get('qa_items_usable', 0)}")
    lines.append(f"Status: {inv.get('status', 'N/A')}")
    lines.append(f"Raw Content Saved: {inv.get('raw_content_saved', False)}")
    lines.append(f"OCR Used: {inv.get('ocr_used', False)}")
    if inv.get("failure_reason"):
        lines.append(f"Failure Reason: {inv['failure_reason']}")
    lines.append("")
    if inv.get("rows"):
        lines.append("## QA Items")
        for row in inv["rows"][:10]:
            q = row.get("question", "")[:80]
            a = row.get("answer", "")[:80]
            lines.append(f"- Q: {q}")
            lines.append(f"  A: {a}")
        if len(inv.get("rows", [])) > 10:
            lines.append(f"- ... and {len(inv['rows']) - 10} more")
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
