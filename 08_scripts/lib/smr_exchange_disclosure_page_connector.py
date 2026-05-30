#!/usr/bin/env python3
"""Phase 71: Exchange disclosure page connector."""
import json, urllib.request, urllib.parse
from typing import Any

def fetch_exchange_disclosure(ticker: str, skip_network: bool = False) -> dict[str, Any]:
    """Fetch exchange disclosure metadata for a ticker."""
    code = ticker.split(".")[0]
    market = "SZ" if "SZ" in ticker else "SH"
    exchange = "SZSE" if market == "SZ" else "SSE"

    if skip_network:
        return {"ticker": ticker, "exchange": exchange, "metadata_found": 0, "status": "skipped_network_disabled", "mock_used": False, "fixture_used": False}

    # SZSE attempt
    if market == "SZ":
        try:
            url = f"https://www.szse.cn/api/disc/announcement/annList?stockCode={code}&pageNum=1&pageSize=20"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = json.loads(resp.read().decode("utf-8", errors="replace"))
            items = body.get("data", body.get("announcements", []))
            metadata_found = len(items) if isinstance(items, list) else 0
            status = "metadata_available" if metadata_found > 0 else "no_results"
            return {"ticker": ticker, "exchange": exchange, "metadata_found": metadata_found, "pdf_or_text_urls_found": metadata_found, "status": status, "mock_used": False, "fixture_used": False}
        except Exception as e:
            return {"ticker": ticker, "exchange": exchange, "metadata_found": 0, "status": "endpoint_failed", "failure_reason": str(e)[:120], "mock_used": False, "fixture_used": False}

    # SSE attempt
    if market == "SH":
        try:
            url = f"https://query.sse.com.cn/security/stock/queryAnnouncement.do?stockCode={code}&page=1&pageSize=20"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": "https://www.sse.com.cn/"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = json.loads(resp.read().decode("utf-8", errors="replace"))
            items = body.get("result", body.get("data", []))
            metadata_found = len(items) if isinstance(items, list) else 0
            status = "metadata_available" if metadata_found > 0 else "no_results"
            return {"ticker": ticker, "exchange": exchange, "metadata_found": metadata_found, "pdf_or_text_urls_found": metadata_found, "status": status, "mock_used": False, "fixture_used": False}
        except Exception as e:
            return {"ticker": ticker, "exchange": exchange, "metadata_found": 0, "status": "endpoint_failed", "failure_reason": str(e)[:120], "mock_used": False, "fixture_used": False}

    return {"ticker": ticker, "exchange": exchange, "metadata_found": 0, "status": "unsupported_market", "mock_used": False, "fixture_used": False}

def build_exchange_report(tickers: list = None) -> dict[str, Any]:
    if tickers is None: tickers = ["300308.SZ", "688041.SH", "300394.SZ"]
    rows = [fetch_exchange_disclosure(t) for t in tickers]
    metadata_ok = sum(1 for r in rows if r.get("metadata_found", 0) > 0)
    return {"exchange_disclosure_report": {"tickers_checked": len(tickers), "metadata_found": metadata_ok, "text_or_pdf_url_found": metadata_ok, "rows": rows, "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}
