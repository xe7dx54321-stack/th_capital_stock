#!/usr/bin/env python3
import argparse, json, sys, io, hashlib
from pathlib import Path
J = Path(__file__).resolve().parent
L = Path(__file__).resolve().parents[1] / "lib"
if str(J) not in sys.path: sys.path.insert(0, str(J))
if str(L) not in sys.path: sys.path.insert(0, str(L))
from run_phase76_688041_pdf_download_recovery import run as run_dl

def extract_pdf_text(pdf_data):
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_data))
        text = "".join((p.extract_text() or "") for p in reader.pages)
        pages = len(reader.pages)
        ch = sum(1 for c in text if "一" <= c <= "鿿")
        cr = round(ch / max(len(text), 1), 3)
        th = "sha256:" + hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]
        qg = "usable_report_text" if len(text) > 500 and cr > 0.05 else ("text_too_short" if len(text) <= 500 else "low_chinese_ratio")
        return {"status": "pdf_text_ok", "text_length": len(text), "pages": pages, "text_hash": th, "chinese_ratio": cr, "quality_grade": qg, "text_preview": text[:3000]}
    except ImportError:
        return {"status": "pdf_text_failed", "failure_reason": "pypdf_not_available"}
    except Exception as e:
        msg = str(e)
        if "encrypted" in msg.lower():
            return {"status": "encrypted_pdf", "failure_reason": msg[:100]}
        return {"status": "pdf_text_failed", "failure_reason": msg[:100]}

def run(mode="execute", max_pdfs=10):
    dl = run_dl(mode, max_pdfs=max_pdfs)
    dlr = dl["phase76_688041_pdf_download_recovery"]
    rows = []
    ok = 0
    for row in dlr.get("rows", []):
        data = row.pop("_data", None)
        if row["download_status"] != "pdf_download_ok" or data is None:
            row["text_extraction_status"] = "skipped_no_pdf_data"
            row["text_length"] = 0
            rows.append(row)
            continue
        er = extract_pdf_text(data)
        row["text_extraction_status"] = er["status"]
        row["text_length"] = er.get("text_length", 0)
        row["text_hash"] = er.get("text_hash", "")
        row["quality_grade"] = er.get("quality_grade", "")
        row["page_count"] = er.get("pages", 0)
        row["chinese_ratio"] = er.get("chinese_ratio", 0)
        if er["status"] == "pdf_text_ok":
            ok += 1
            row["text_preview"] = er.get("text_preview", "")
        rows.append(row)
    usable = sum(1 for r in rows if r.get("quality_grade", "").startswith("usable"))
    return {"phase76_688041_pdf_text_extraction": {
        "ticker": dlr.get("ticker", "688041.SH"), "pdfs_checked": len(rows),
        "pdf_text_ok": ok, "pdf_text_failed": len(rows) - ok,
        "texts_usable_for_evidence": usable, "rows": rows,
        "raw_pdf_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False
    }}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true")
    p.add_argument("--max-pdfs", type=int, default=10); p.add_argument("--json", action="store_true")
    a = p.parse_args()
    mode = "dry_run" if getattr(a, "dry_run") else "execute"
    r = run(mode, max_pdfs=a.max_pdfs)
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
