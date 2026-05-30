#!/usr/bin/env python3
import argparse, json, sys, urllib.request
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_phase76_known_url_breakthrough import load_candidates, verify_candidates

def fetch_url(url, timeout=30):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"}, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            ct = resp.headers.get("Content-Type", "")
        return {"http_status": status, "content_type": ct, "reachable": True}
    except urllib.error.HTTPError as e:
        return {"http_status": e.code, "content_type": "", "reachable": False, "error": str(e)[:100]}
    except Exception as e:
        return {"http_status": 0, "content_type": "", "reachable": False, "error": str(e)[:100]}

def run(mode="execute", ticker="300394.SZ"):
    if mode == "dry_run":
        return {"phase76_300394_known_url_fetch": {"ticker": ticker, "network_attempted": False, "urls_checked": 0, "http_ok": 0, "rows": [], "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}
    if mode == "skip_network":
        candidates = load_candidates(ticker)
        rows = [{"title": c.get("title", ""), "url": c.get("url", ""), "url_status": "skip_network"} for c in candidates]
        return {"phase76_300394_known_url_fetch": {"ticker": ticker, "network_attempted": False, "urls_checked": len(rows), "http_ok": 0, "rows": rows, "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}
    candidates = load_candidates(ticker)
    verified = verify_candidates(candidates)
    rows = []
    ok = 0
    for c in verified:
        url = c.get("url", "")
        if not url or not c.get("verification_status", "").startswith("verified"):
            rows.append({"title": c.get("title", ""), "url": url, "url_status": "not_verified", "content_type": "", "fetch_error": c.get("verification_status", "")})
            continue
        fr = fetch_url(url)
        is_pdf = "pdf" in fr.get("content_type", "").lower()
        is_html = "html" in fr.get("content_type", "").lower()
        if fr["reachable"]:
            ok += 1
        rows.append({
            "title": c.get("title", ""), "url": url,
            "url_status": f"http_{fr['http_status']}" if fr["reachable"] else "unreachable",
            "content_type": fr.get("content_type", ""),
            "is_pdf": is_pdf, "is_html": is_html,
            "allowed_usage": c.get("allowed_usage", "business_context"),
            "fetch_error": fr.get("error")
        })
    return {"phase76_300394_known_url_fetch": {
        "ticker": ticker, "network_attempted": True, "urls_checked": len(rows),
        "http_ok": ok, "html_pages_fetched": sum(1 for r in rows if r.get("is_html") and r["url_status"].startswith("http_2")),
        "pdf_urls_fetched": sum(1 for r in rows if r.get("is_pdf") and r["url_status"].startswith("http_2")),
        "text_or_pdf_available": ok, "rows": rows,
        "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False
    }}

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
