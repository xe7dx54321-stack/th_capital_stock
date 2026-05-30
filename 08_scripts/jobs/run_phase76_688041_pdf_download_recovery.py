#!/usr/bin/env python3
import argparse, json, sys, io, urllib.request, urllib.parse
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES

CNINFO_API = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json",
    "Referer": "https://www.cninfo.com.cn/", "Content-Type": "application/x-www-form-urlencoded"}

def download_pdf(url, timeout=40):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.cninfo.com.cn/"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        content_type = resp.headers.get("Content-Type", "")
        if "html" in content_type.lower() or data[:100].strip().startswith(b"<!DOCTYPE") or data[:100].strip().startswith(b"<html"):
            return {"status": "html_error_instead_of_pdf", "content_type": content_type, "data_len": len(data), "_data": None}
        if not data[:5] == b"%PDF-":
            return {"status": "not_pdf_magic_header", "content_type": content_type, "data_len": len(data), "_data": None}
        return {"status": "pdf_download_ok", "content_type": content_type, "data_len": len(data), "_data": data}
    except Exception as e:
        return {"status": "download_failed", "failure_reason": str(e)[:100], "data_len": 0, "_data": None}

def run(mode="execute", ticker="688041.SH", max_pdfs=10):
    sn = mode == "skip_network"
    ident = CURATED_CNINFO_IDENTITIES.get(ticker, {})
    if not ident:
        return {"phase76_688041_pdf_download_recovery": {"ticker": ticker, "status": "identity_not_found", "pdf_download_ok": 0, "rows": [], "mock_used": False, "fixture_used": False}}
    if mode == "dry_run":
        return {"phase76_688041_pdf_download_recovery": {"ticker": ticker, "network_attempted": False, "pdfs_selected": max_pdfs, "pdf_download_ok": 0, "rows": [], "raw_pdf_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}
    if sn:
        return {"phase76_688041_pdf_download_recovery": {"ticker": ticker, "network_attempted": False, "pdfs_selected": 0, "pdf_download_ok": 0, "rows": [], "status": "skip_network", "raw_pdf_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}
    try:
        params = {"pageNum": 1, "pageSize": min(max_pdfs, 10), "stock": ident["security_code"] + "," + ident["org_id"],
            "plate": ident.get("plate", "sh"), "column": ident.get("column", "sse"),
            "tabName": "fulltext", "searchkey": "", "secid": "", "category": "", "trade": "", "seDate": ""}
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(CNINFO_API, data=data, headers=dict(HEADERS))
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as e:
        return {"phase76_688041_pdf_download_recovery": {"ticker": ticker, "network_attempted": True, "pdfs_selected": 0, "pdf_download_ok": 0, "rows": [], "status": "cninfo_api_failed", "failure_reason": str(e)[:100], "raw_pdf_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}
    rows = []
    ok = 0
    for ann in body.get("announcements", [])[:max_pdfs]:
        title = (ann.get("announcementTitle", "") or "")[:120]
        rel = ann.get("adjunctUrl", "")
        if not rel:
            rows.append({"title": title, "download_status": "no_pdf_url", "data_len": 0, "failure_reason": "no_adjunctUrl"})
            continue
        full = "https://static.cninfo.com.cn/" + rel if not rel.startswith("http") else rel
        dr = download_pdf(full)
        row = {"title": title, "download_status": dr["status"], "content_type": dr.get("content_type", ""),
            "data_len": dr.get("data_len", 0), "download_temp_or_ignored_path_used": True,
            "failure_reason": dr.get("failure_reason"), "_data": dr.get("_data")}
        if dr["status"] == "pdf_download_ok":
            ok += 1
        rows.append(row)
    return {"phase76_688041_pdf_download_recovery": {
        "ticker": ticker, "network_attempted": True, "pdfs_selected": len(rows),
        "pdf_download_attempted": sum(1 for r in rows if r["download_status"] != "no_pdf_url"),
        "pdf_download_ok": ok, "pdf_download_failed": len(rows) - ok,
        "rows": rows, "raw_pdf_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False
    }}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true")
    p.add_argument("--skip-network", action="store_true"); p.add_argument("--max-pdfs", type=int, default=10)
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    mode = "skip_network" if getattr(a, "skip_network") else ("dry_run" if getattr(a, "dry_run") else "execute")
    r = run(mode, max_pdfs=a.max_pdfs)
    dr = r["phase76_688041_pdf_download_recovery"]
    out = {"ticker": dr["ticker"], "network_attempted": dr.get("network_attempted", True),
        "pdfs_selected": dr.get("pdfs_selected", 0), "pdf_download_ok": dr.get("pdf_download_ok", 0),
        "pdf_download_failed": dr.get("pdf_download_failed", 0),
        "rows": [{"title": row["title"], "download_status": row["download_status"],
                  "data_len": row.get("data_len", 0), "failure_reason": row.get("failure_reason")} for row in dr.get("rows", [])],
        "raw_pdf_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}
    print(json.dumps({"phase76_688041_pdf_download_recovery": out}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
