#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_phase74_sse_html_disclosure_parser import parse_sse_html
from smr_phase75_real_execute_config import load_config

def run(mode="execute", tickers=None):
    if tickers is None:
        cfg = load_config()
        tickers = cfg["sources"]["sse_html"]["tickers"]
    sn = mode == "skip_network"
    network_attempted = mode == "execute"
    if mode == "dry_run":
        rows = [{"ticker": t, "status": "dry_run", "network_attempted": False} for t in tickers]
        return {"phase75_sse_html_real_execute": {"mode": mode, "network_attempted": False,
            "tickers_checked": len(tickers), "html_fetch_attempted": 0, "html_pages_fetched": 0,
            "announcement_links_found": 0, "pdf_links_found": 0, "text_pages_found": 0, "rows": rows,
            "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}
    rows = [parse_sse_html(t, skip_network=sn) for t in tickers]
    for r in rows:
        r["network_attempted"] = network_attempted
    fetched = sum(r.get("html_pages_fetched", 0) for r in rows)
    links = sum(r.get("announcement_links_found", 0) for r in rows)
    pdfs = sum(r.get("pdf_links_found", 0) for r in rows)
    texts = sum(r.get("text_pages_found", 0) for r in rows)
    first_row = rows[0] if rows else {}
    return {"phase75_sse_html_real_execute": {"mode": mode, "network_attempted": network_attempted,
        "ticker": tickers[0] if tickers else "", "tickers_checked": len(tickers),
        "html_fetch_attempted": len(tickers), "html_pages_fetched": fetched,
        "announcement_links_found": links, "pdf_links_found": pdfs, "text_pages_found": texts,
        "rows": rows, "texts": first_row.get("texts", []),
        "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true")
    p.add_argument("--skip-network", action="store_true"); p.add_argument("--json", action="store_true")
    a = p.parse_args()
    mode = "skip_network" if getattr(a, "skip_network") else ("dry_run" if getattr(a, "dry_run") else "execute")
    r = run(mode)
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
