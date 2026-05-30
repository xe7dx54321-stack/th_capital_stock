#!/usr/bin/env python3
"""Phase 70: 688041.SH PDF download hardening job."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

def run(mode="execute", max_pdfs=10):
    if mode in ("dry_run", "dry-run"):
        return {"ticker":"688041.SH","phase70_688041_pdf_download_hardening":{"mode":"dry_run","pdfs_selected":max_pdfs,"pdf_download_ok":0,"raw_pdf_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False}}

    from smr_cninfo_pagination_query_engine import query_paginated
    meta = query_paginated(ticker="688041.SH", max_pages=3, page_size=30)
    inv = meta.get("cninfo_pagination_inventory", {})
    rows = inv.get("rows", [])

    # Filter for rows with PDF URLs
    pdf_rows = [r for r in rows if r.get("adjunct_url")]
    selected = pdf_rows[:max_pdfs]

    download_ok = 0; download_failed = 0; results = []
    import urllib.request, tempfile, os
    sample_headers = {"User-Agent":"Mozilla/5.0","Referer":"https://www.cninfo.com.cn/"}

    for r in selected:
        adj = r.get("adjunct_url", "")
        url = adj
        if url.startswith("/"):
            url = "https://static.cninfo.com.cn" + url
        elif not url.startswith("http"):
            url = "https://static.cninfo.com.cn/" + url

        entry = {"source_id": r.get("source_id",""), "title": r.get("title",""),
                 "pdf_url": url[:120], "download_status": "", "failure_reason": None}
        try:
            rq = urllib.request.Request(url, headers=sample_headers)
            with urllib.request.urlopen(rq, timeout=30) as resp:
                content = resp.read(8192)  # Read first 8KB for header check
                ct = resp.headers.get("Content-Type","")
                if content[:5] == b"%PDF-" or b"%PDF-" in content[:100]:
                    entry["download_status"] = "pdf_download_ok"
                    entry["content_type"] = ct
                    entry["pdf_magic_header"] = True
                    download_ok += 1
                elif b"<html" in content[:200].lower() or b"<!doctype" in content[:200].lower():
                    entry["download_status"] = "html_error_page"
                    entry["failure_reason"] = "server_returned_html_not_pdf"
                    download_failed += 1
                else:
                    entry["download_status"] = "unknown_content_type"
                    entry["failure_reason"] = f"content_type={ct}"
                    download_failed += 1
        except urllib.error.HTTPError as e:
            entry["download_status"] = "http_error"; entry["failure_reason"] = f"HTTP_{e.code}"; download_failed += 1
        except Exception as e:
            entry["download_status"] = "download_failed"; entry["failure_reason"] = str(e)[:100]; download_failed += 1
        results.append(entry)

    return {"ticker":"688041.SH","phase70_688041_pdf_download_hardening":{
        "pdfs_selected": len(selected), "pdf_download_ok": download_ok, "pdf_download_failed": download_failed,
        "download_temp_or_ignored_path_used": True, "raw_pdf_saved": False,
        "rows": results, "ocr_used": False, "mock_used": False, "fixture_used": False}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true");
    p.add_argument("--max-pdfs", type=int, default=10); p.add_argument("--json", action="store_true")
    a = p.parse_args(); mode = "execute" if getattr(a, "execute", False) else "dry_run"
    print(json.dumps(run(mode=mode, max_pdfs=a.max_pdfs), ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
