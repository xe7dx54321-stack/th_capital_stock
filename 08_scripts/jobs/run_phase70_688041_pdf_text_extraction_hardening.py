#!/usr/bin/env python3
"""Phase 70: 688041.SH PDF text extraction hardening job."""
import argparse, json, sys, hashlib
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

def run(mode="execute", max_pdfs=10):
    if mode in ("dry_run", "dry-run"):
        return {"ticker":"688041.SH","phase70_688041_pdf_text_extraction":{"mode":"dry_run","pdfs_checked":0,"pdf_text_ok":0,"raw_pdf_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False}}

    from smr_cninfo_pagination_query_engine import query_paginated
    meta = query_paginated(ticker="688041.SH", max_pages=3, page_size=30)
    inv = meta.get("cninfo_pagination_inventory", {})
    rows = inv.get("rows", [])
    pdf_rows = [r for r in rows if r.get("adjunct_url")][:max_pdfs]

    import urllib.request, tempfile, os
    sample_headers = {"User-Agent":"Mozilla/5.0","Referer":"https://www.cninfo.com.cn/"}

    pdf_text_ok = 0; pdf_text_failed = 0; results = []
    for r in pdf_rows:
        adj = r.get("adjunct_url", "")
        url = adj
        if url.startswith("/"): url = "https://static.cninfo.com.cn" + url
        elif not url.startswith("http"): url = "https://static.cninfo.com.cn/" + url

        entry = {"source_id": r.get("source_id",""), "title": r.get("title",""),
                 "text_extraction_status": "", "page_count": 0, "text_length": 0, "text_hash": "",
                 "quality_hint": "", "failure_reason": None}

        try:
            rq = urllib.request.Request(url, headers=sample_headers)
            with urllib.request.urlopen(rq, timeout=30) as resp:
                content = resp.read()
            if len(content) < 100: entry["failure_reason"] = "response_too_small"; pdf_text_failed += 1; results.append(entry); continue
            if content[:5] != b"%PDF-" and b"%PDF-" not in content[:100]:
                entry["failure_reason"] = "not_a_pdf"; pdf_text_failed += 1; results.append(entry); continue

            # Write temp file for pypdf
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.write(content); tmp.close()

            try:
                import pypdf
                reader = pypdf.PdfReader(tmp.name)
                entry["page_count"] = len(reader.pages)
                text_parts = []
                for page in reader.pages:
                    pt = page.extract_text()
                    if pt: text_parts.append(pt)
                full_text = "\n".join(text_parts).strip()
                entry["text_length"] = len(full_text)
                entry["text_hash"] = "sha256:" + hashlib.sha256(full_text.encode("utf-8")).hexdigest()[:16]
                if len(full_text) >= 200:
                    entry["text_extraction_status"] = "pdf_text_ok"
                    entry["quality_hint"] = "usable_report_text" if len(full_text) > 5000 else "short_text"
                    pdf_text_ok += 1
                else:
                    entry["text_extraction_status"] = "pdf_text_failed"
                    entry["failure_reason"] = "text_too_short"; pdf_text_failed += 1
            except Exception as e:
                entry["text_extraction_status"] = "pdf_text_failed"
                entry["failure_reason"] = f"pypdf_error: {str(e)[:80]}"; pdf_text_failed += 1
            finally:
                try: os.unlink(tmp.name)
                except: pass
        except urllib.error.HTTPError as e:
            entry["failure_reason"] = f"HTTP_{e.code}"; pdf_text_failed += 1
        except Exception as e:
            entry["failure_reason"] = str(e)[:100]; pdf_text_failed += 1
        results.append(entry)

    usable = sum(1 for r in results if r["text_extraction_status"] == "pdf_text_ok")
    return {"ticker":"688041.SH","phase70_688041_pdf_text_extraction":{
        "pdfs_checked": len(results), "pdf_text_ok": pdf_text_ok, "pdf_text_failed": pdf_text_failed,
        "texts_written": pdf_text_ok, "texts_usable_for_evidence": usable,
        "rows": results, "raw_pdf_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true");
    p.add_argument("--max-pdfs", type=int, default=10); p.add_argument("--json", action="store_true")
    a = p.parse_args(); mode = "execute" if getattr(a, "execute", False) else "dry_run"
    print(json.dumps(run(mode=mode, max_pdfs=a.max_pdfs), ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
