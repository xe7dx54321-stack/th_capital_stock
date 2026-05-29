#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_disclosure_source_fallback_router import route_disclosure_source

def build(ticker="300308.SZ", skip_network=False):
    return route_disclosure_source(ticker, skip_network=skip_network)

def _md(result):
    r = result.get("disclosure_source_fallback_router", result)
    lines = [f"# Disclosure Source Fallback Router: {result.get('ticker', 'N/A')}", ""]
    lines.append(f"Selected Primary Source: {r.get('selected_primary_source', 'N/A')}")
    lines.append(f"CNINFO Status: {r.get('cninfo_status', 'N/A')}")
    lines.append(f"SZSE Status: {r.get('szse_status', 'N/A')}")
    lines.append(f"IRM Status: {r.get('irm_status', 'N/A')}")
    lines.append(f"Company Site Status: {r.get('company_site_status', 'N/A')}")
    lines.append(f"Real Metadata Available: {r.get('real_metadata_available', False)}")
    lines.append(f"Real Text Available: {r.get('real_text_available', False)}")
    lines.append(f"Fallback Used: {r.get('fallback_used', False)}")
    lines.append(f"Mock Used: {r.get('mock_used', False)}")
    lines.append(f"Fixture Used: {r.get('fixture_used', False)}")
    lines.append("")
    lines.append("## Routing Reasons")
    for reason in r.get("routing_reason", []):
        lines.append(f"- {reason}")
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
