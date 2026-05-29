#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

from smr_disclosure_source_fallback_router import route_disclosure_source

def build(ticker="300308.SZ", skip_network=False):
    router = route_disclosure_source(ticker, skip_network=skip_network)
    r = router.get("disclosure_source_fallback_router", router)

    # Determine best available path
    best_path = "none"
    if r.get("irm_status") == "qa_available":
        best_path = "szse_metadata_plus_irm_qa" if r.get("szse_status") == "metadata_available" else "irm_qa_only"
    elif r.get("szse_status") == "metadata_available":
        best_path = "szse_metadata_only"
    elif r.get("cninfo_status", "").startswith("reachable"):
        best_path = "cninfo_metadata_only_zero_results"

    return {
        "summary": {
            "ticker": ticker,
            "cninfo": {
                "reachable": r.get("cninfo_status", "unknown").startswith("reachable"),
                "metadata_available": r.get("cninfo_status", "unknown").startswith("reachable"),
                "text_available": False,
                "failure_reason": "zero_results_or_unreachable" if r.get("cninfo_status") != "unreachable" else "cninfo_unreachable",
            },
            "szse": {
                "reachable": r.get("szse_status", "unknown") != "unreachable",
                "metadata_available": r.get("szse_status") == "metadata_available",
                "text_available": False,
                "pdf_url_available": r.get("szse_status") == "metadata_available",
                "failure_reason": None if r.get("szse_status") == "metadata_available" else "szse_api_http_500",
            },
            "irm": {
                "reachable": r.get("irm_status", "unknown") != "unreachable",
                "qa_available": r.get("irm_status") == "qa_available",
                "api_json_available": False,
                "html_parse_available": r.get("irm_status") == "qa_available",
                "failure_reason": None if r.get("irm_status") == "qa_available" else "irm_html_not_extractable",
            },
            "company_site": {
                "configured": False,
                "failure_reason": "url_not_configured",
            },
            "best_available_path": best_path,
            "real_source_usable": r.get("real_metadata_available", False) or r.get("real_text_available", False),
            "mock_used": False,
            "fixture_used": False,
            "raw_saved": False,
            "ocr_used": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
        }
    }

def _md(result):
    s = result.get("summary", result)
    lines = ["# Connector Health Dashboard", ""]
    lines.append(f"Ticker: {s.get('ticker', 'N/A')}")
    lines.append(f"Best Available Path: {s.get('best_available_path', 'N/A')}")
    lines.append(f"Real Source Usable: {s.get('real_source_usable', False)}")
    lines.append(f"Mock/Fixture: {s.get('mock_used', False)}/{s.get('fixture_used', False)}")
    lines.append(f"Raw/OCR: {s.get('raw_saved', False)}/{s.get('ocr_used', False)}")
    lines.append(f"Pending/Order/Trade: {s.get('pending_created', 0)}/{s.get('paper_order_created', 0)}/{s.get('real_trade_created', 0)}")
    lines.append("")
    for name in ["cninfo", "szse", "irm", "company_site"]:
        c = s.get(name, {})
        lines.append(f"## {name.upper()}")
        for k, v in c.items():
            lines.append(f"- {k}: {v}")
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
