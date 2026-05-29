#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_small_controlled_source_fetch import run_small_controlled_source_fetch

def build(ticker="300308.SZ", skip_network=False):
    return run_small_controlled_source_fetch(ticker, max_sources=10, mode="execute", skip_network=skip_network)

def _md(result):
    r = result.get("small_controlled_source_fetch", result)
    lines = [f"# Small Controlled Source Fetch Report: {result.get('ticker', 'N/A')}", ""]
    lines.append(f"Network Attempted: {r.get('network_attempted', False)}")
    lines.append(f"Mode: {r.get('mode', 'N/A')}")
    lines.append(f"Status: {r.get('status', 'N/A')}")
    lines.append(f"Selected Sources: {', '.join(r.get('selected_sources', []))}")
    lines.append(f"Sources Checked: {r.get('sources_checked', 0)}")
    lines.append(f"Metadata OK: {r.get('metadata_ok', 0)}")
    lines.append(f"Text OK: {r.get('text_ok', 0)}")
    lines.append(f"PDF URL OK: {r.get('pdf_url_ok', 0)}")
    lines.append(f"PDF Text OK: {r.get('pdf_text_ok', 0)}")
    lines.append(f"Metadata Only: {r.get('metadata_only', 0)}")
    lines.append(f"Failed: {r.get('failed', 0)}")
    lines.append(f"Mock Used: {r.get('mock_used', False)}")
    lines.append(f"Fixture Used: {r.get('fixture_used', False)}")
    lines.append(f"Raw Saved: {r.get('raw_saved', False)}")
    lines.append(f"OCR Used: {r.get('ocr_used', False)}")
    lines.append("")
    if r.get("rows"):
        lines.append("## Source Details")
        for row in r["rows"]:
            lines.append(f"- {row.get('source_id', '')}: {row.get('fetch_status', '')}")
            if row.get("failure_reason"):
                lines.append(f"  Failure: {row['failure_reason']}")
            if row.get("qa_count"):
                lines.append(f"  QA Count: {row['qa_count']}")
        lines.append("")
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ticker",default="300308.SZ")
    p.add_argument("--json",action="store_true")
    p.add_argument("--markdown",action="store_true")
    p.add_argument("--skip-network",action="store_true")
    args=p.parse_args()
    result=build(args.ticker, getattr(args,"skip_network",False))
    if args.json: print(json.dumps(result,ensure_ascii=False,indent=2))
    elif args.markdown: print(_md(result))
    else: print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
