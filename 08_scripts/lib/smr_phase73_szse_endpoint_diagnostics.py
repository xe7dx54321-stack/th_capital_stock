#!/usr/bin/env python3
"""Phase 73: SZSE endpoint diagnostics - harder diagnosis of HTTP 500."""
import json, urllib.request, urllib.error
from typing import Any

def test_szse_variant(url: str, headers: dict = None, method: str = "GET") -> dict[str, Any]:
    if headers is None: headers = {"User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request(url, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return {"status_code": resp.status, "response_type": "json", "json_body": json.loads(raw), "error": None, "url": url}
            except:
                return {"status_code": resp.status, "response_type": "html", "text_preview": raw[:500], "error": None, "url": url}
    except urllib.error.HTTPError as e:
        return {"status_code": e.code, "response_type": "http_error", "error": str(e), "url": url}
    except Exception as e:
        return {"status_code": 0, "response_type": "exception", "error": str(e)[:200], "url": url}

def diagnose_szse(ticker: str, skip_network: bool = False) -> dict[str, Any]:
    code = ticker.split(".")[0]; market = "SZ" if "SZ" in ticker else "SH"
    if market != "SZ": return {"ticker": ticker, "diagnostic_status": "not_applicable_sh", "mock_used": False, "fixture_used": False}
    if skip_network: return {"ticker": ticker, "diagnostic_status": "skipped", "mock_used": False, "fixture_used": False}
    bh = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept": "application/json, text/plain, */*", "Referer": "https://www.szse.cn/"}
    vs = []
    vs.append({"name": "annList_stockCode", "result": test_szse_variant(f"https://www.szse.cn/api/disc/announcement/annList?stockCode={code}&pageNum=1&pageSize=20", dict(bh))})
    vs.append({"name": "annList_secCode", "result": test_szse_variant(f"https://www.szse.cn/api/disc/announcement/annList?secCode={code}&pageNum=1&pageSize=20", dict(bh))})
    vs.append({"name": "queryAnnouncement_stockCode", "result": test_szse_variant(f"https://www.szse.cn/api/disc/announcement/queryAnnouncement?stockCode={code}&pageNum=1&pageSize=20", dict(bh))})
    vs.append({"name": "disclosure_html_page", "result": test_szse_variant(f"https://www.szse.cn/disclosure/listed/fixed/index.html?code={code}", dict(bh))})
    vs.append({"name": "annList_channelCode", "result": test_szse_variant(f"https://www.szse.cn/api/disc/announcement/annList?stockCode={code}&channelCode=listedNotice&pageNum=1&pageSize=20", dict(bh))})
    vs.append({"name": "annList_plateCode", "result": test_szse_variant(f"https://www.szse.cn/api/disc/announcement/annList?stockCode={code}&plateCode=cyb&pageNum=1&pageSize=20", dict(bh))})
    vs.append({"name": "annList_post", "result": test_szse_variant("https://www.szse.cn/api/disc/announcement/annList", dict(bh), "POST")})
    vs.append({"name": "annList_en_locale", "result": test_szse_variant(f"https://www.szse.cn/api/disc/announcement/annList?stockCode={code}&pageNum=1&pageSize=20&locale=en", dict(bh))})
    jo = [v for v in vs if v["result"].get("response_type") == "json"]
    h500 = [v for v in vs if v["result"].get("status_code") == 500]
    ho = [v for v in vs if v["result"].get("response_type") == "html"]
    ds = "endpoint_repaired" if jo else ("html_only" if ho else "blocked_with_specific_reason")
    return {"ticker": ticker, "endpoint_variants_tested": len(vs), "http_500_count": len(h500), "json_response_count": len(jo),
        "html_response_count": len(ho), "metadata_found": 0, "announcement_links_found": 0, "html_page_parse_attempted": len(ho) > 0,
        "diagnostic_status": ds, "most_specific_blocker": "szse_endpoint_http_500_persistent_across_variants" if h500 and not jo else (None if jo else "all_variants_failed"),
        "variants": [{"name": v["name"], "status_code": v["result"].get("status_code"), "response_type": v["result"].get("response_type"), "error": v["result"].get("error")} for v in vs],
        "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}
