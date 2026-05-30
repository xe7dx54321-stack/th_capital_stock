#!/usr/bin/env python3
"""Phase 73: SSE endpoint repair - diagnose and fix HTTP 404."""
import json, urllib.request, urllib.error
from typing import Any

def test_sse_variant(url: str, headers: dict = None) -> dict[str, Any]:
    if headers is None: headers = {"User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try: return {"status_code": resp.status, "response_type": "json", "json_body": json.loads(raw), "error": None, "url": url}
            except: return {"status_code": resp.status, "response_type": "html", "text_preview": raw[:1000], "error": None, "url": url}
    except urllib.error.HTTPError as e:
        return {"status_code": e.code, "response_type": "http_error", "error": str(e), "url": url}
    except Exception as e:
        return {"status_code": 0, "response_type": "exception", "error": str(e)[:200], "url": url}

def repair_sse(ticker: str, skip_network: bool = False) -> dict[str, Any]:
    code = ticker.split(".")[0]; market = "SH" if "SH" in ticker else "SZ"
    if market != "SH": return {"ticker": ticker, "repair_status": "not_applicable_sz", "mock_used": False, "fixture_used": False}
    if skip_network: return {"ticker": ticker, "repair_status": "skipped", "mock_used": False, "fixture_used": False}
    bh = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept": "application/json, text/html", "Referer": "https://www.sse.com.cn/"}
    vs = []
    vs.append({"name": "query_do_stockCode", "result": test_sse_variant(f"https://query.sse.com.cn/security/stock/queryAnnouncement.do?stockCode={code}&page=1&pageSize=20", dict(bh))})
    vs.append({"name": "shtml_announcement_page", "result": test_sse_variant(f"https://www.sse.com.cn/assortment/stock/list/info/announcement/index.shtml?stockCode={code}", dict(bh))})
    vs.append({"name": "query_do_code", "result": test_sse_variant(f"https://query.sse.com.cn/security/stock/queryAnnouncement.do?code={code}&page=1&pageSize=20", dict(bh))})
    vs.append({"name": "query_do_pagination", "result": test_sse_variant(f"https://query.sse.com.cn/security/stock/queryAnnouncement.do?stockCode={code}&isPagination=true&pageHelp.pageNo=1&pageHelp.pageSize=20", dict(bh))})
    vs.append({"name": "shtml_company_code", "result": test_sse_variant(f"https://www.sse.com.cn/assortment/stock/list/info/announcement/index.shtml?COMPANY_CODE={code}", dict(bh))})
    vs.append({"name": "disclosure_listed_info", "result": test_sse_variant(f"https://www.sse.com.cn/disclosure/listedinfo/announcement/s_docdatesort_desc_{code}.htm", dict(bh))})
    vs.append({"name": "star_board_announcement", "result": test_sse_variant(f"https://star.sse.com.cn/star/announcement/queryAnnouncement.do?stockCode={code}", dict(bh))})
    h8 = dict(bh); h8["Accept"] = "application/json"
    vs.append({"name": "query_do_json_accept", "result": test_sse_variant(f"https://query.sse.com.cn/security/stock/queryAnnouncement.do?stockCode={code}", h8)})
    jo = [v for v in vs if v["result"].get("response_type") == "json"]
    ho = [v for v in vs if v["result"].get("response_type") == "html"]
    n404 = [v for v in vs if v["result"].get("status_code") == 404]
    n200 = [v for v in vs if v["result"].get("status_code") == 200]
    mf = 0
    if jo:
        b = jo[0]["result"].get("json_body", {})
        items = b.get("result", b.get("data", b.get("announcements", [])))
        if isinstance(items, list): mf = len(items)
    rs = "endpoint_repaired" if jo else ("html_page_available" if ho else "not_repaired")
    return {"ticker": ticker, "endpoint_variants_tested": len(vs), "http_200_count": len(n200), "http_404_count": len(n404),
        "json_response_count": len(jo), "html_response_count": len(ho), "metadata_found": mf, "pdf_or_text_urls_found": 0, "text_pages_found": 0,
        "repair_status": rs, "failure_reason": "all_sse_endpoints_return_404_or_no_results" if not (jo or ho) else None,
        "most_specific_blocker": None if (jo or ho) else "sse_disclosure_api_path_or_company_code_unknown",
        "variants": [{"name": v["name"], "status_code": v["result"].get("status_code"), "response_type": v["result"].get("response_type"), "error": v["result"].get("error")} for v in vs],
        "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}
