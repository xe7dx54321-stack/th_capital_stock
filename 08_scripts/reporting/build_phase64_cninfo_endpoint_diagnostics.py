#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_cninfo_endpoint_diagnostics import run_cninfo_diagnostics

def build(ticker="300308.SZ", skip_network=False):
    return run_cninfo_diagnostics(ticker, skip_network=skip_network)

def _md(result):
    d = result.get("cninfo_endpoint_diagnostics", result)
    lines = [f"# CNINFO Endpoint Diagnostics: {result.get('ticker', 'N/A')}", ""]
    lines.append(f"Network Attempted: {d.get('network_attempted', False)}")
    lines.append(f"DNS OK: {d.get('dns_ok', 'N/A')}")
    if d.get("dns_failure_reason"):
        lines.append(f"DNS Failure: {d['dns_failure_reason']}")
    lines.append(f"HTTPS Connect OK: {d.get('https_connect_ok', 'N/A')}")
    if d.get("https_connect_failure_reason"):
        lines.append(f"HTTPS Failure: {d['https_connect_failure_reason']}")
    lines.append("")

    aq = d.get("his_announcement_query", {})
    if aq.get("tests"):
        lines.append("## Announcement Query Tests")
        lines.append("")
        for t in aq.get("tests", []):
            lines.append(f"### {t.get('test_label', 'unknown_test')}")
            lines.append(f"- Status: {t.get('status', 'N/A')}")
            lines.append(f"- HTTP: {t.get('http_status', 'N/A')}")
            lines.append(f"- Response Type: {t.get('response_type', 'N/A')}")
            lines.append(f"- Response Length: {t.get('response_length', 0)}")
            if t.get("failure_reason"):
                lines.append(f"- Failure: {t['failure_reason']}")
            if t.get("status") == "ok" and t.get("response_json"):
                rj = t["response_json"]
                lines.append(f"- Total Announcements: {rj.get('totalAnnouncement', 0)}")
            lines.append("")

    dp = d.get("disclosure_page", {})
    if dp:
        lines.append("## Disclosure Page")
        lines.append(f"- Status: {dp.get('status', 'N/A')}")
        lines.append(f"- HTTP: {dp.get('http_status', 'N/A')}")
        if dp.get("failure_reason"):
            lines.append(f"- Failure: {dp['failure_reason']}")
        lines.append("")

    lines.append("## Root Cause Analysis")
    lines.append(f"- Likely Root Cause: {d.get('likely_root_cause', 'N/A')}")
    lines.append(f"- Recommended Next Action: {d.get('recommended_next_action', 'N/A')}")
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ticker",default="300308.SZ")
    p.add_argument("--json",action="store_true")
    p.add_argument("--markdown",action="store_true")
    p.add_argument("--skip-network",action="store_true")
    args=p.parse_args()
    result=build(args.ticker, skip_network=getattr(args,"skip_network",False))
    if args.json: print(json.dumps(result,ensure_ascii=False,indent=2))
    elif args.markdown: print(_md(result))
    else: print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
