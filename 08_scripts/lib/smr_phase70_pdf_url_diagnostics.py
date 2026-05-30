#!/usr/bin/env python3
"""Phase 70: PDF URL diagnostics for 688041.SH."""
import json, urllib.request, urllib.parse
from typing import Any

CNINFO_API = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
HEADERS = {"User-Agent":"Mozilla/5.0","Accept":"application/json","Referer":"https://www.cninfo.com.cn/","Content-Type":"application/x-www-form-urlencoded"}

def diagnose_pdf_urls(ticker="688041.SH", org_id="9900048365", plate="sh", column="sse", max_sample=5) -> dict[str, Any]:
    """Diagnose PDF URL availability and health for a ticker."""
    code = ticker.split(".")[0]
    stock_param = f"{code},{org_id}"

    # 1. Fetch metadata
    metadata_rows = []
    try:
        for page in range(1, 4):
            params = {"pageNum":page, "pageSize":30, "stock":stock_param, "plate":plate,
                      "column":column, "tabName":"fulltext", "searchkey":"", "secid":"",
                      "category":"", "trade":"", "seDate":""}
            data = urllib.parse.urlencode(params).encode()
            req = urllib.request.Request(CNINFO_API, data=data, headers=dict(HEADERS))
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = json.loads(resp.read().decode("utf-8", errors="replace"))
            anns = body.get("announcements", [])
            if not anns:
                continue
            for a in anns:
                metadata_rows.append(a)
    except Exception as e:
        return build_diag_result(ticker, [], f"metadata_fetch_failed: {str(e)[:100]}")

    # 2. Extract PDF URLs
    pdf_urls = []
    for row in metadata_rows:
        adj = row.get("adjunctUrl", "")
        if adj:
            url = adj
            if url.startswith("/"):
                url = "https://static.cninfo.com.cn" + url
            elif not url.startswith("http"):
                url = "https://static.cninfo.com.cn/" + url
            pdf_urls.append({"source_id": str(row.get("announcementId","")),
                            "title": row.get("announcementTitle",""),
                            "pdf_url": url,
                            "adjunct_raw": adj})

    # 3. Check URL format
    missing = len(metadata_rows) - len(pdf_urls)
    relative = sum(1 for p in pdf_urls if p["adjunct_raw"].startswith("/"))
    absolute = sum(1 for p in pdf_urls if p["adjunct_raw"].startswith("http"))
    static_cninfo = sum(1 for p in pdf_urls if "static.cninfo.com.cn" in p["pdf_url"])

    # 4. Sample HEAD/GET check
    head_ok = 0; get_ok = 0; html_error = 0; timeout_count = 0; ssl_error = 0
    pdf_like = 0; failures = []
    sample = pdf_urls[:max_sample]
    sample_headers = {"User-Agent":"Mozilla/5.0","Referer":"https://www.cninfo.com.cn/"}
    for p in sample:
        try:
            rq = urllib.request.Request(p["pdf_url"], headers=sample_headers, method="HEAD")
            with urllib.request.urlopen(rq, timeout=15) as resp:
                ct = resp.headers.get("Content-Type","")
                if resp.status == 200:
                    head_ok += 1
                    if "pdf" in ct.lower() or "octet-stream" in ct.lower():
                        pdf_like += 1
                elif resp.status >= 400:
                    html_error += 1
                    failures.append({"url_short": p["pdf_url"][-60:], "status": resp.status, "content_type": ct})
        except urllib.error.HTTPError as e:
            html_error += 1
            failures.append({"url_short": p["pdf_url"][-60:], "status": e.code, "error": "http_error"})
        except urllib.error.URLError as e:
            if "SSL" in str(e.reason).upper() or "CERTIFICATE" in str(e.reason).upper():
                ssl_error += 1
            failures.append({"url_short": p["pdf_url"][-60:], "error": str(e.reason)[:80]})
        except TimeoutError:
            timeout_count += 1
            failures.append({"url_short": p["pdf_url"][-60:], "error": "timeout"})
        except Exception as e:
            failures.append({"url_short": p["pdf_url"][-60:], "error": str(e)[:80]})

    # 5. Build diagnosis
    top_failures = list(set(f["error"] for f in failures))[:5]
    recs = []
    if timeout_count > 0:
        recs.append("increase_timeout_for_pdf_download")
    if html_error > 0:
        recs.append("check_referer_or_cookie_requirement")
    if ssl_error > 0:
        recs.append("check_certificate_or_use_verify_ssl_false")
    if head_ok > 0 and pdf_like == 0:
        recs.append("check_content_type_sniffing")

    return build_diag_result(ticker, metadata_rows, None, pdf_urls, missing, relative, absolute, static_cninfo,
                            head_ok, get_ok, html_error, timeout_count, ssl_error, pdf_like, failures, top_failures, recs)

def build_diag_result(ticker, metadata_rows, fetch_error=None, pdf_urls=None, missing=0, relative=0, absolute=0, static_cninfo=0,
                      head_ok=0, get_ok=0, html_error=0, timeout_count=0, ssl_error=0, pdf_like=0, failures=None, top_failures=None, recs=None):
    if fetch_error:
        return {"ticker":ticker, "phase70_688041_pdf_url_diagnostics": {
            "metadata_sources_checked": 0, "pdf_urls_found": 0, "failure_reason": fetch_error,
            "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}
    return {"ticker":ticker, "phase70_688041_pdf_url_diagnostics": {
        "metadata_sources_checked": len(metadata_rows), "pdf_urls_found": len(pdf_urls or []),
        "pdf_urls_valid_format": len(pdf_urls or []), "pdf_urls_missing": missing,
        "relative_url_count": relative, "absolute_url_count": absolute, "static_cninfo_url_count": static_cninfo,
        "sample_checked": len(failures or []) + head_ok,
        "pdf_urls_head_ok": head_ok, "pdf_urls_get_ok": get_ok,
        "html_error_response": html_error, "timeout_count": timeout_count, "ssl_error_count": ssl_error,
        "pdf_like_response": pdf_like, "top_failure_reasons": top_failures or [],
        "recommended_fix": recs or [], "sample_failures": failures or [],
        "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}
