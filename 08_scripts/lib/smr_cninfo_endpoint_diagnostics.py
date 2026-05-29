#!/usr/bin/env python3
"""CNINFO endpoint diagnostics for Phase 64."""

from __future__ import annotations

import json
import socket
import ssl
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Any


CNINFO_HOST = "www.cninfo.com.cn"
CNINFO_ANNOUNCEMENT_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
CNINFO_DISCLOSURE_URL = "https://www.cninfo.com.cn/new/disclosure"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.cninfo.com.cn/",
}


def _test_dns(host: str, timeout: int = 5) -> dict[str, Any]:
    """Test DNS resolution for a host."""
    try:
        ip = socket.getaddrinfo(host, 443, socket.AF_INET, socket.SOCK_STREAM)
        return {"dns_ok": True, "resolved_ips": list(set(a[4][0] for a in ip))}
    except socket.gaierror as e:
        return {"dns_ok": False, "failure_reason": f"DNS resolution failed: {e}"}
    except Exception as e:
        return {"dns_ok": False, "failure_reason": str(e)}


def _test_https_connect(host: str, timeout: int = 10) -> dict[str, Any]:
    """Test HTTPS connectivity to a host."""
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                return {"https_connect_ok": True, "ssl_version": ssock.version()}
    except socket.timeout:
        return {"https_connect_ok": False, "failure_reason": "connection_timed_out"}
    except ConnectionRefusedError:
        return {"https_connect_ok": False, "failure_reason": "connection_refused"}
    except Exception as e:
        return {"https_connect_ok": False, "failure_reason": str(e)}


def _make_request(
    url: str,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 20,
) -> dict[str, Any]:
    """Make an HTTP request and record the result."""
    if headers is None:
        headers = dict(DEFAULT_HEADERS)
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
            content = resp.read()
            result["response_length"] = len(content)
            ct = resp.getheader("Content-Type", "")
            if "json" in ct:
                result["response_type"] = "json"
                try:
                    result["response_json"] = json.loads(content.decode("utf-8", errors="replace"))
                except json.JSONDecodeError:
                    result["response_type"] = "text"
            elif "html" in ct:
                result["response_type"] = "html"
            else:
                result["response_type"] = "binary_or_text"
            result["status"] = "ok"
    except urllib.error.HTTPError as e:
        result["http_status"] = e.code
        result["status"] = "failed"
        result["failure_reason"] = f"http_error_{e.code}"
        try:
            body = e.read()
            result["response_length"] = len(body)
        except Exception:
            pass
    except urllib.error.URLError as e:
        result["status"] = "failed"
        reason_str = str(e.reason)
        if "timed out" in reason_str.lower():
            result["failure_reason"] = "connection_timed_out"
        elif "getaddrinfo" in reason_str.lower():
            result["failure_reason"] = "dns_resolution_failed"
        elif "certificate" in reason_str.lower():
            result["failure_reason"] = "ssl_certificate_error"
        elif "403" in reason_str:
            result["failure_reason"] = "forbidden_403"
            result["http_status"] = 403
        else:
            result["failure_reason"] = f"url_error: {reason_str}"
    except Exception as e:
        result["status"] = "failed"
        result["failure_reason"] = str(e)
    return result


def _test_cninfo_announcement_query(ticker: str, timeout: int = 20) -> dict[str, Any]:
    """Test CNINFO announcement query endpoint."""
    results = {"endpoint": CNINFO_ANNOUNCEMENT_URL, "tests": []}

    # Extract stock code from ticker (e.g., 300308.SZ -> 300308)
    code = ticker.split(".")[0] if "." in ticker else ticker

    # Test 1: standard params
    params1 = {
        "pageNum": "1",
        "pageSize": "30",
        "column": "szse",
        "tabName": "fulltext",
        "plate": "sz",
        "stock": code,
        "searchkey": "",
        "secid": "",
        "category": "",
        "trade": "",
        "seDate": "",
    }
    encoded1 = urllib.parse.urlencode(params1).encode("utf-8")
    headers1 = dict(DEFAULT_HEADERS)
    headers1["Content-Type"] = "application/x-www-form-urlencoded"
    result1 = _make_request(CNINFO_ANNOUNCEMENT_URL, "POST", encoded1, headers1, timeout)
    result1["params"] = params1
    result1["test_label"] = "standard_params"
    results["tests"].append(result1)

    # Test 2: with secid parameter
    params2 = {
        "pageNum": "1",
        "pageSize": "30",
        "column": "szse",
        "tabName": "fulltext",
        "plate": "sz",
        "stock": "",
        "searchkey": "",
        "secid": f"300308",
        "category": "",
        "trade": "",
        "seDate": "",
    }
    encoded2 = urllib.parse.urlencode(params2).encode("utf-8")
    result2 = _make_request(CNINFO_ANNOUNCEMENT_URL, "POST", encoded2, headers1, timeout)
    result2["params"] = params2
    result2["test_label"] = "secid_param"
    results["tests"].append(result2)

    # Test 3: with just stock code and searchkey
    params3 = {
        "pageNum": "1",
        "pageSize": "30",
        "column": "szse",
        "tabName": "fulltext",
        "plate": "sz",
        "stock": code,
        "searchkey": code,
        "secid": "",
        "category": "",
        "trade": "",
        "seDate": "",
    }
    encoded3 = urllib.parse.urlencode(params3).encode("utf-8")
    result3 = _make_request(CNINFO_ANNOUNCEMENT_URL, "POST", encoded3, headers1, timeout)
    result3["params"] = params3
    result3["test_label"] = "searchkey_param"
    results["tests"].append(result3)

    return results


def _test_cninfo_disclosure_page(timeout: int = 20) -> dict[str, Any]:
    """Test CNINFO disclosure page."""
    return _make_request(CNINFO_DISCLOSURE_URL, "GET", None, dict(DEFAULT_HEADERS), timeout)


def run_cninfo_diagnostics(ticker: str = "300308.SZ", skip_network: bool = False) -> dict[str, Any]:
    """Run full CNINFO endpoint diagnostics."""
    diag: dict[str, Any] = {
        "ticker": ticker,
        "cninfo_endpoint_diagnostics": {
            "network_attempted": not skip_network,
            "dns_ok": None,
            "https_connect_ok": None,
            "his_announcement_query": {},
            "disclosure_page": {},
            "likely_root_cause": "not_diagnosed",
            "recommended_next_action": "not_determined",
        },
    }

    d = diag["cninfo_endpoint_diagnostics"]

    if skip_network:
        d["dns_ok"] = False
        d["https_connect_ok"] = False
        d["status"] = "skipped_network_disabled"
        d["likely_root_cause"] = "skip_network_enabled"
        d["recommended_next_action"] = "run with network enabled to diagnose"
        return diag

    # DNS test
    dns_result = _test_dns(CNINFO_HOST)
    d["dns_ok"] = dns_result.get("dns_ok")
    if not dns_result.get("dns_ok"):
        d["dns_failure_reason"] = dns_result.get("failure_reason")
        d["likely_root_cause"] = "dns_resolution_failed"
        d["recommended_next_action"] = "check_network_or_dns_configuration"
        return diag

    # HTTPS connect test
    https_result = _test_https_connect(CNINFO_HOST)
    d["https_connect_ok"] = https_result.get("https_connect_ok")
    if not https_result.get("https_connect_ok"):
        d["https_connect_failure_reason"] = https_result.get("failure_reason")
        d["likely_root_cause"] = "cninfo_unreachable_or_blocked_in_current_network"
        d["recommended_next_action"] = "try_cninfo_from_mainland_network_or_use_szse_fallback"
        return diag

    # Test announcement query
    d["his_announcement_query"] = _test_cninfo_announcement_query(ticker)

    # Test disclosure page
    d["disclosure_page"] = _test_cninfo_disclosure_page()

    # Determine root cause
    ann_ok = any(t.get("status") == "ok" for t in d["his_announcement_query"].get("tests", []))
    ann_has_results = any(
        t.get("status") == "ok"
        and t.get("response_json", {}).get("totalAnnouncement", 0) > 0
        for t in d["his_announcement_query"].get("tests", [])
    )

    if ann_has_results:
        d["likely_root_cause"] = "cninfo_working"
        d["recommended_next_action"] = "use_cninfo_as_primary_disclosure_source"
    elif ann_ok:
        d["likely_root_cause"] = "cninfo_api_reachable_but_params_or_query_filters_need_adjustment"
        d["recommended_next_action"] = "try_different_stock_code_formats_or_discover_correct_params"
    else:
        d["likely_root_cause"] = "cninfo_unreachable_or_blocked_in_current_network"
        d["recommended_next_action"] = "try_cninfo_from_mainland_network_or_use_szse_fallback"

    return diag
