#!/usr/bin/env python3
"""Phase 71: IRM / Interactive Q&A connector."""
import json, urllib.request, urllib.parse
from typing import Any

IRM_API = "https://irm.cninfo.com.cn/ircs/interaction/getInteraction"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": "https://irm.cninfo.com.cn/", "Content-Type": "application/x-www-form-urlencoded"}

def fetch_irm_qa(ticker: str, max_items: int = 20, skip_network: bool = False) -> dict[str, Any]:
    """Fetch IRM QA items for a ticker."""
    code = ticker.split(".")[0]
    market = "SZ" if "SZ" in ticker else "SH"

    if market != "SZ":
        return {"ticker": ticker, "market": market, "irm_supported": False, "qa_items_found": 0, "status": "use_sse_equivalent_required", "mock_used": False, "fixture_used": False}

    if skip_network:
        return {"ticker": ticker, "market": market, "irm_supported": True, "qa_items_found": 0, "status": "skipped_network_disabled", "mock_used": False, "fixture_used": False}

    try:
        params = {"stock": code, "pageNum": 1, "pageSize": max_items}
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(IRM_API, data=data, headers=dict(HEADERS))
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode("utf-8", errors="replace"))

        if isinstance(body, dict):
            items = body.get("data", body.get("rows", body.get("items", [])))
        elif isinstance(body, list):
            items = body
        else:
            return {"ticker": ticker, "market": market, "irm_supported": True, "qa_items_found": 0, "status": "html_returned_instead_of_json", "failure_reason": "unexpected_response_type", "mock_used": False, "fixture_used": False}

        qa_items = []
        for item in items:
            question = item.get("question", item.get("q", ""))
            answer = item.get("answer", item.get("a", ""))
            if question or answer:
                qa_items.append({"question": str(question)[:500], "answer": str(answer)[:2000], "date": str(item.get("date", item.get("publishDate", "")))})

        return {"ticker": ticker, "market": market, "irm_supported": True, "qa_items_found": len(qa_items), "qa_text_available": sum(1 for q in qa_items if q["answer"]), "items": qa_items, "status": "qa_text_available" if qa_items else "no_qa_found", "mock_used": False, "fixture_used": False}
    except Exception as e:
        return {"ticker": ticker, "market": market, "irm_supported": True, "qa_items_found": 0, "status": "endpoint_failed", "failure_reason": str(e)[:120], "mock_used": False, "fixture_used": False}

def build_irm_report(tickers: list = None) -> dict[str, Any]:
    if tickers is None: tickers = ["300308.SZ", "688041.SH", "300394.SZ"]
    rows = [fetch_irm_qa(t) for t in tickers]
    return {"irm_interaction_report": {"tickers_checked": len(tickers), "rows": rows, "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}
