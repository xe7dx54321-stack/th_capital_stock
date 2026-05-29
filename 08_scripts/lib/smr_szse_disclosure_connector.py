#!/usr/bin/env python3
"""SZSE disclosure connector for Phase 64. Tries to fetch disclosure metadata from SZSE."""

from __future__ import annotations

import json
import urllib.request
import urllib.error
import urllib.parse
import hashlib
from typing import Any

SZSE_MAIN = "https://www.szse.cn"
SZSE_DISCLOSURE_API = "https://www.szse.cn/api/disc/announcement/annList"
SZSE_DISCLOSURE_PAGE = "https://www.szse.cn/disclosure/index.html"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.szse.cn/",
}


def _check_szse_reachable(timeout: int = 15) -> dict[str, Any]:
    """Check if SZSE main site is reachable."""
    try:
        req = urllib.request.Request(SZSE_MAIN, headers=DEFAULT_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            return {
                "szse_reachable": True,
                "http_status": resp.status,
                "response_length": len(body),
            }
    except Exception as e:
        return {"szse_reachable": False, "failure_reason": str(e)}


def _try_disclosure_api(method: str, params: dict[str, str], timeout: int = 15) -> dict[str, Any]:
    """Try SZSE disclosure API with given method and params."""
    result = {"method": method, "attempted": True, "http_status": None, "status": "unknown", "failure_reason": None}
    headers = dict(DEFAULT_HEADERS)
    data = None
    try:
        if method == "GET":
            url = SZSE_DISCLOSURE_API + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers=headers)
        elif method == "POST_JSON":
            headers["Content-Type"] = "application/json"
            data = json.dumps(params).encode("utf-8")
            req = urllib.request.Request(SZSE_DISCLOSURE_API, data=data, headers=headers)
        elif method == "POST_FORM":
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            data = urllib.parse.urlencode(params).encode("utf-8")
            req = urllib.request.Request(SZSE_DISCLOSURE_API, data=data, headers=headers)
        else:
            result["status"] = "skipped"
            result["failure_reason"] = f"unsupported_method: {method}"
            return result
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result["http_status"] = resp.status
            body = resp.read()
            result["response_length"] = len(body)
            if resp.status == 200:
                ct = resp.getheader("Content-Type", "")
                result["content_type"] = ct
                if "json" in ct:
                    try:
                        result["response_json"] = json.loads(body.decode("utf-8", errors="replace"))
                        result["status"] = "ok"
                    except json.JSONDecodeError:
                        result["status"] = "parse_failed"
                        result["failure_reason"] = "json_decode_error"
                else:
                    result["status"] = "unexpected_content_type"
                    result["failure_reason"] = f"not_json: {ct}"
            else:
                result["status"] = "failed"
                result["failure_reason"] = f"http_{resp.status}"
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


def fetch_szse_disclosure(
    ticker: str = "300308.SZ",
    max_sources: int = 15,
    mode: str = "execute",
    skip_network: bool = False,
) -> dict[str, Any]:
    """Fetch disclosure metadata from SZSE."""
    code = ticker.split(".")[0] if "." in ticker else ticker

    result: dict[str, Any] = {
        "ticker": ticker,
        "szse_disclosure_inventory": {
            "network_attempted": not skip_network,
            "mode": mode,
            "szse_reachable": False,
            "metadata_sources_found": 0,
            "source_types": {},
            "pdf_urls_found": 0,
            "text_urls_found": 0,
            "raw_content_saved": False,
            "ocr_used": False,
            "mock_used": False,
            "fixture_used": False,
            "rows": [],
            "status": "pending",
        },
    }

    inv = result["szse_disclosure_inventory"]

    if skip_network:
        inv["status"] = "skipped_network_disabled"
        inv["failure_reason"] = "skip_network_enabled"
        return result

    if mode == "dry-run":
        # Simulate what would be attempted
        params = {"stock": [code], "pageNum": 1, "pageSize": 30}
        inv["status"] = "dry_run"
        inv["would_attempt"] = {
            "endpoint": SZSE_DISCLOSURE_API,
            "methods_to_try": ["GET", "POST_JSON", "POST_FORM"],
            "params_example": params,
            "max_sources": max_sources,
        }
        return result

    # Check reachability
    reach = _check_szse_reachable()
    inv["szse_reachable"] = reach.get("szse_reachable", False)
    if not inv["szse_reachable"]:
        inv["status"] = "szse_not_reachable"
        inv["failure_reason"] = reach.get("failure_reason", "unknown")
        return result

    # Try disclosure API with multiple methods
    base_params = {"stock": [code], "pageNum": 1, "pageSize": 30, "channelCode": ["listedNotice_disc"]}

    methods_tried = []
    for method in ["GET", "POST_JSON", "POST_FORM"]:
        api_result = _try_disclosure_api(method, base_params)
        methods_tried.append(api_result)
        if api_result.get("status") == "ok" and api_result.get("response_json"):
            rj = api_result["response_json"]
            announcements = rj.get("data", rj.get("announcements", rj.get("result", [])))
            if not isinstance(announcements, list):
                announcements = []
            inv["metadata_sources_found"] = len(announcements)
            for ann in announcements:
                row = {
                    "source_id": f"szse_{code}_{ann.get('id', 'unknown')}",
                    "source_type": _classify_szse_type(ann),
                    "title": ann.get("title", ann.get("secName", "")),
                    "publish_date": ann.get("publishDate", ann.get("announceTime", "")),
                    "url": ann.get("adjunctUrl", ann.get("url", "")),
                    "pdf_url": ann.get("adjunctUrl", ""),
                    "fetch_status": "metadata_ok",
                    "allowed_usage": "metadata_only_until_text_extracted",
                }
                if row["pdf_url"]:
                    inv["pdf_urls_found"] += 1
                inv["rows"].append(row)
            inv["status"] = "metadata_ok"
            break
        elif api_result.get("http_status") == 500:
            inv["status"] = f"http_500_on_{method}"
        else:
            continue

    if inv["metadata_sources_found"] == 0 and inv["status"].startswith("http_500"):
        inv["status"] = "szse_reachable_but_disclosure_api_returns_500"
        inv["failure_reason"] = "szse_disclosure_api_http_500_all_methods"
        inv["methods_tried"] = methods_tried

    if inv["metadata_sources_found"] == 0 and inv["status"] == "pending":
        inv["status"] = "site_reachable_but_disclosure_endpoint_not_identified"
        inv["failure_reason"] = "endpoint_not_found_or_response_unstructured"
        inv["methods_tried"] = methods_tried

    return result


def _classify_szse_type(ann: dict[str, Any]) -> str:
    """Classify SZSE announcement into a source type."""
    title = (ann.get("title", "") or ann.get("secName", "")).lower()
    if "年度报告" in title or "annual report" in title:
        return "annual_report"
    elif "半年度报告" in title or "semi" in title:
        return "semiannual_report"
    elif "季度报告" in title or "季报" in title:
        return "quarterly_report"
    elif "投资者关系" in title or "调研" in title or "ir" in title:
        return "investor_relations_record"
    else:
        return "announcement"
