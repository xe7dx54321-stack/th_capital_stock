#!/usr/bin/env python3
"""Phase 73: IRM endpoint repair - diagnose and fix HTTP 405."""
import json, urllib.request, urllib.parse, urllib.error
from typing import Any

IRM_BASE = "https://irm.cninfo.com.cn/ircs/interaction"

def test_endpoint_variant(url: str, method: str = "POST", headers: dict = None, body_data: dict = None) -> dict[str, Any]:
    if headers is None: headers = {}
    try:
        data = urllib.parse.urlencode(body_data or {}).encode() if body_data else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return {"status_code": resp.status, "response_type": "json", "json_body": json.loads(raw), "error": None}
            except:
                return {"status_code": resp.status, "response_type": "html", "text_preview": raw[:500], "error": None}
    except urllib.error.HTTPError as e:
        allow = e.headers.get("Allow", e.headers.get("allow", ""))
        return {"status_code": e.code, "response_type": "http_error", "error": str(e), "allow_header": allow, "url": url, "method": method}
    except Exception as e:
        return {"status_code": 0, "response_type": "exception", "error": str(e)[:200]}

def repair_irm(ticker: str, skip_network: bool = False) -> dict[str, Any]:
    code = ticker.split(".")[0]
    market = "SZ" if "SZ" in ticker else "SH"
    if market != "SZ":
        return {"ticker": ticker, "irm_supported": False, "repair_status": "not_applicable_sh", "mock_used": False, "fixture_used": False}
    if skip_network:
        return {"ticker": ticker, "repair_status": "skipped", "mock_used": False, "fixture_used": False}

    base_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "application/json, text/plain, */*", "Referer": "https://irm.cninfo.com.cn/", "Origin": "https://irm.cninfo.com.cn", "X-Requested-With": "XMLHttpRequest"}
    variants = []

    h1 = dict(base_headers); h1["Content-Type"] = "application/x-www-form-urlencoded"
    r1 = test_endpoint_variant(f"{IRM_BASE}/getInteraction", "POST", h1, {"stock": code, "pageNum": 1, "pageSize": 20})
    variants.append({"name": "post_form_stock", "endpoint": f"{IRM_BASE}/getInteraction", "method": "POST", "result": r1})

    r2 = test_endpoint_variant(f"{IRM_BASE}/getInteraction", "POST", h1, {"companyCode": code, "pageNum": 1, "pageSize": 20})
    variants.append({"name": "post_form_companyCode", "endpoint": f"{IRM_BASE}/getInteraction", "method": "POST", "result": r2})

    h3 = dict(base_headers); h3["Content-Type"] = "application/json"
    r3 = test_endpoint_variant(f"{IRM_BASE}/getInteraction", "POST", h3, None)
    variants.append({"name": "post_json_stock", "endpoint": f"{IRM_BASE}/getInteraction", "method": "POST", "result": r3})

    h4 = dict(base_headers)
    r4 = test_endpoint_variant(f"{IRM_BASE}/getInteraction?stock={code}&pageNum=1&pageSize=20", "GET", h4)
    variants.append({"name": "get_query_stock", "endpoint": f"{IRM_BASE}/getInteraction", "method": "GET", "result": r4})

    r5 = test_endpoint_variant(f"{IRM_BASE}/query", "POST", h1, {"stock": code, "pageNum": 1, "pageSize": 20})
    variants.append({"name": "post_form_query_endpoint", "endpoint": f"{IRM_BASE}/query", "method": "POST", "result": r5})

    r6 = test_endpoint_variant(f"{IRM_BASE}/question?stock={code}", "GET", h4)
    variants.append({"name": "get_question_endpoint", "endpoint": f"{IRM_BASE}/question", "method": "GET", "result": r6})

    r7 = test_endpoint_variant(f"{IRM_BASE}/getInteraction", "POST", h1, {"securityCode": code, "pageNo": 1, "pageSize": 20})
    variants.append({"name": "post_securityCode_pageNo", "endpoint": f"{IRM_BASE}/getInteraction", "method": "POST", "result": r7})

    h8 = dict(base_headers); h8["Content-Type"] = "application/x-www-form-urlencoded"
    del h8["Referer"]; del h8["Origin"]
    r8 = test_endpoint_variant(f"{IRM_BASE}/getInteraction", "POST", h8, {"stock": code, "pageNum": 1, "pageSize": 20})
    variants.append({"name": "post_no_referer", "endpoint": f"{IRM_BASE}/getInteraction", "method": "POST", "result": r8})

    json_ok = [v for v in variants if v["result"].get("response_type") == "json"]
    http_405 = [v for v in variants if v["result"].get("status_code") == 405]
    html_ok = [v for v in variants if v["result"].get("response_type") == "html"]

    qa_text_usable = 0
    if json_ok:
        body = json_ok[0]["result"].get("json_body", {})
        items = body.get("data", body.get("rows", body.get("items", body.get("result", []))))
        if isinstance(items, dict): items = list(items.values())
        if isinstance(items, list):
            qa_text_usable = sum(1 for it in items if isinstance(it, dict) and (it.get("answer") or it.get("a") or "").strip())

    repair_status = "endpoint_repaired" if json_ok else ("html_only" if html_ok else "not_repaired")
    failure_reason = None
    if not json_ok:
        if http_405:
            failure_reason = "all_post_variants_return_http_405_allow:" + str(http_405[0]["result"].get("allow_header", "unknown"))
        else:
            failure_reason = "all_endpoint_variants_failed_or_returned_html"

    return {
        "ticker": ticker, "endpoint_variants_tested": len(variants),
        "method_variants_tested": ["GET", "POST"],
        "http_405_count": len(http_405), "json_response_count": len(json_ok),
        "html_response_count": len(html_ok), "qa_items_found": len(json_ok),
        "qa_text_usable": qa_text_usable, "repair_status": repair_status,
        "failure_reason": failure_reason,
        "most_specific_blocker": failure_reason if not json_ok else None,
        "variants": [{"name": v["name"], "status_code": v["result"].get("status_code"), "response_type": v["result"].get("response_type"), "error": v["result"].get("error")} for v in variants],
        "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False
    }
