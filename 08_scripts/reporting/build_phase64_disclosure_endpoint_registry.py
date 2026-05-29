#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_a_share_disclosure_endpoint_registry import get_endpoint_summary

def build(): return get_endpoint_summary()

def _md(result):
    lines = ["# A-Share Disclosure Source Endpoint Registry", ""]
    meta = result.get("meta", {})
    lines.append(f"Phase: {meta.get('phase', 'N/A')} | Version: {meta.get('version', 'N/A')}")
    lines.append(f"Total Sources: {result.get('total_sources', 0)}")
    lines.append(f"Platforms: {', '.join(result.get('platforms', []))}")
    lines.append(f"Raw Content Saved: {result.get('raw_content_saved_all', False)}")
    lines.append(f"OCR Allowed: {result.get('ocr_allowed_all', False)}")
    lines.append("")
    for src in result.get("sources", []):
        lines.append(f"## {src['source_id']}")
        lines.append(f"- Platform: {src['platform']}")
        lines.append(f"- Endpoint: {src['endpoint_type']}")
        lines.append(f"- Method: {src['method']}")
        lines.append(f"- URL: {src.get('url', 'N/A')}")
        lines.append(f"- Fallback Priority: {src.get('fallback_priority', 'N/A')}")
        lines.append(f"- Allowed Usage: {src.get('allowed_usage', 'N/A')}")
        if src.get("notes"):
            lines.append(f"- Notes: {src['notes']}")
        lines.append("")
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--json",action="store_true")
    p.add_argument("--markdown",action="store_true")
    args=p.parse_args()
    result=build()
    if args.json: print(json.dumps(result,ensure_ascii=False,indent=2))
    elif args.markdown: print(_md(result))
    else: print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
