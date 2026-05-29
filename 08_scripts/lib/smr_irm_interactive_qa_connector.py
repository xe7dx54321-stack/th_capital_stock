#!/usr/bin/env python3
"""IRM interactive QA connector for Phase 64. Handles HTML fallback for QA extraction."""

from __future__ import annotations

import json
import re
import urllib.request
import urllib.error
import urllib.parse
import hashlib
from typing import Any

IRM_BASE = "https://irm.cninfo.com.cn"
IRM_QUESTIONS_API = "https://irm.cninfo.com.cn/ircs/interaction/questions"
IRM_MAIN = "https://irm.cninfo.com.cn"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://irm.cninfo.com.cn/",
}


def _make_request(url: str, method: str = "GET", data: bytes | None = None, timeout: int = 20) -> dict[str, Any]:
    """Make HTTP request and return structured result."""
    headers = dict(DEFAULT_HEADERS)
    if data:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    result = {
        "url": url,
        "method": method,
        "attempted": True,
        "http_status": None,
        "status": "unknown",
        "response_type": "none",
        "response_length": 0,
        "failure_reason": None,
    }
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result["http_status"] = resp.status
            body = resp.read()
            result["response_length"] = len(body)
            ct = resp.getheader("Content-Type", "")
            decoded = body.decode("utf-8", errors="replace")
            if "json" in ct:
                result["response_type"] = "json"
                try:
                    result["response_json"] = json.loads(decoded)
                except json.JSONDecodeError:
                    result["response_type"] = "html"
                    result["response_html"] = decoded
            elif "html" in ct:
                result["response_type"] = "html"
                result["response_html"] = decoded
            else:
                result["response_type"] = "text"
                result["response_html"] = decoded
            result["status"] = "ok"
    except urllib.error.HTTPError as e:
        result["http_status"] = e.code
        result["status"] = "failed"
        result["failure_reason"] = f"http_error_{e.code}"
    except urllib.error.URLError as e:
        result["status"] = "failed"
        result["failure_reason"] = f"url_error: {e.reason}"
    except Exception as e:
        result["status"] = "failed"
        result["failure_reason"] = str(e)
    return result


def _parse_qa_from_html(html: str) -> list[dict[str, Any]]:
    """Parse QA pairs from IRM HTML response. Conservative extraction only."""
    qa_items: list[dict[str, Any]] = []

    # Try to find question-answer patterns in the HTML
    # Pattern 1: div with question/answer classes
    qa_patterns = [
        # Common IRM HTML structures
        (r'<div[^>]*class="[^"]*question[^"]*"[^>]*>(.*?)</div>', r'<div[^>]*class="[^"]*answer[^"]*"[^>]*>(.*?)</div>'),
        (r'<div[^>]*class="[^"]*qa_q[^"]*"[^>]*>(.*?)</div>', r'<div[^>]*class="[^"]*qa_a[^"]*"[^>]*>(.*?)</div>'),
        (r'questionTitle["\']?\s*[：:]\s*(.*?)</', r'answerContent["\']?\s*[：:]\s*(.*?)</'),
    ]

    for q_pat, a_pat in qa_patterns:
        questions = re.findall(q_pat, html, re.DOTALL | re.IGNORECASE)
        answers = re.findall(a_pat, html, re.DOTALL | re.IGNORECASE)
        for i in range(min(len(questions), len(answers))):
            q_clean = _clean_html(questions[i])
            a_clean = _clean_html(answers[i])
            if q_clean and a_clean:
                qa_items.append({"question": q_clean, "answer": a_clean})

    # Pattern 2: Look for structured JSON data embedded in the HTML
    json_patterns = [
        r'questionsList["\']?\s*[:=]\s*(\[.*?\])',
        r'"data"\s*:\s*(\[.*?\])',
        r'qaList["\']?\s*[:=]\s*(\[.*?\])',
    ]
    for jp in json_patterns:
        matches = re.findall(jp, html, re.DOTALL)
        for m in matches:
            try:
                parsed = json.loads(m)
                if isinstance(parsed, list):
                    for item in parsed:
                        q = item.get("question", item.get("title", item.get("q", "")))
                        a = item.get("answer", item.get("content", item.get("a", "")))
                        if q and a:
                            qa_items.append({"question": _clean_html(str(q)), "answer": _clean_html(str(a))})
            except (json.JSONDecodeError, TypeError):
                pass

    # Deduplicate by question text hash
    seen = set()
    unique = []
    for item in qa_items:
        h = hashlib.sha256(item["question"].encode()).hexdigest()
        if h not in seen:
            seen.add(h)
            unique.append(item)
    return unique


def _clean_html(text: str) -> str:
    """Remove HTML tags and normalize whitespace."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Remove HTML entities
    text = re.sub(r'&[a-z]+;', ' ', text)
    text = re.sub(r'&#\d+;', ' ', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def fetch_irm_qa(
    ticker: str = "300308.SZ",
    max_sources: int = 10,
    mode: str = "execute",
    skip_network: bool = False,
) -> dict[str, Any]:
    """Fetch IRM interactive QA for a ticker."""
    code = ticker.split(".")[0] if "." in ticker else ticker

    result: dict[str, Any] = {
        "ticker": ticker,
        "irm_qa_inventory": {
            "network_attempted": not skip_network,
            "mode": mode,
            "irm_reachable": False,
            "api_json_available": False,
            "html_parse_available": False,
            "qa_items_found": 0,
            "qa_items_usable": 0,
            "rows": [],
            "raw_content_saved": False,
            "ocr_used": False,
            "mock_used": False,
            "fixture_used": False,
            "status": "pending",
        },
    }

    inv = result["irm_qa_inventory"]

    if skip_network:
        inv["status"] = "skipped_network_disabled"
        inv["failure_reason"] = "skip_network_enabled"
        return result

    if mode == "dry-run":
        inv["status"] = "dry_run"
        inv["would_attempt"] = {
            "endpoint": IRM_QUESTIONS_API,
            "methods": ["GET", "POST"],
            "parse_methods": ["json_api", "html_fallback"],
            "max_sources": max_sources,
            "ticker_code": code,
        }
        return result

    # Try GET request to questions API
    params = {
        "stock": code,
        "pageNum": 1,
        "pageSize": max_sources,
    }
    url_with_params = IRM_QUESTIONS_API + "?" + urllib.parse.urlencode(params)

    get_result = _make_request(url_with_params, "GET")
    inv["irm_reachable"] = get_result.get("http_status") == 200

    if not inv["irm_reachable"]:
        inv["status"] = "irm_not_reachable"
        inv["failure_reason"] = get_result.get("failure_reason", f"http_{get_result.get('http_status')}")
        return result

    if get_result.get("response_type") == "json":
        inv["api_json_available"] = True
        rj = get_result.get("response_json", {})
        items = rj.get("data", rj.get("questions", rj.get("list", [])))
        if isinstance(items, list):
            for item in items:
                q = item.get("question", item.get("title", ""))
                a = item.get("answer", item.get("content", ""))
                if q and a:
                    qa_item = {
                        "source_id": f"irm_{code}_qa_{item.get('id', len(inv['rows']))}",
                        "question": q,
                        "answer": a,
                        "publish_date": item.get("publishDate", item.get("date", "")),
                        "source_type": "irm_interactive_qa",
                        "text_available": True,
                        "allowed_usage": "real_business_source_text",
                    }
                    inv["rows"].append(qa_item)
            inv["qa_items_found"] = len(inv["rows"])
            inv["qa_items_usable"] = inv["qa_items_found"]
            inv["status"] = "qa_available_json"
            return result

    # HTML fallback
    if get_result.get("response_type") in ("html", "text"):
        inv["html_parse_available"] = True
        html = get_result.get("response_html", "")
        qa_items = _parse_qa_from_html(html)
        inv["qa_items_found"] = len(qa_items)
        for i, item in enumerate(qa_items):
            if item.get("question") and item.get("answer"):
                qa_row = {
                    "source_id": f"irm_{code}_qa_{i}",
                    "question": item["question"],
                    "answer": item["answer"],
                    "publish_date": "",
                    "source_type": "irm_interactive_qa",
                    "text_available": True,
                    "allowed_usage": "real_business_source_text",
                }
                inv["rows"].append(qa_row)
        inv["qa_items_usable"] = len(inv["rows"])
        if inv["qa_items_usable"] > 0:
            inv["status"] = "qa_available_html_parsed"
        else:
            inv["status"] = "irm_reachable_but_qa_not_extractable"
            inv["failure_reason"] = "html_structure_not_supported"
            inv["html_sample_length"] = len(html)
    else:
        inv["status"] = "irm_reachable_but_qa_not_extractable"
        inv["failure_reason"] = f"unexpected_response_type: {get_result.get('response_type')}"

    return result
