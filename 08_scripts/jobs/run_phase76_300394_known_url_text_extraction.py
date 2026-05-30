#!/usr/bin/env python3
import argparse, json, sys, io, urllib.request, hashlib
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_phase74_html_parser_utils import extract_visible_text, remove_boilerplate, text_hash, chinese_ratio

def extract_from_url(url, content_type=""):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        is_pdf = "pdf" in content_type.lower() or data[:5] == b"%PDF-"
        if is_pdf:
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(data))
                text = "".join((p.extract_text() or "") for p in reader.pages)
                pages = len(reader.pages)
            except ImportError:
                return {"status": "pypdf_not_available", "text_length": 0}
            except Exception:
                return {"status": "pdf_extract_failed", "text_length": 0}
        else:
            html = data.decode("utf-8", errors="replace")
            text = remove_boilerplate(extract_visible_text(html))
            pages = 0
        ch = sum(1 for c in text if "一" <= c <= "鿿")
        cr = round(ch / max(len(text), 1), 3)
        th = text_hash(text)
        qg = "usable_business_context" if len(text) > 200 and cr > 0.05 else ("text_too_short" if len(text) <= 200 else "low_chinese_ratio")
        return {"status": "text_ok", "text_length": len(text), "text_hash": th, "chinese_ratio": cr, "quality_grade": qg, "pages": pages, "text_preview": text[:3000]}
    except Exception as e:
        return {"status": "fetch_or_extract_failed", "text_length": 0, "error": str(e)[:100]}

def run(mode="execute"):
    if mode == "dry_run":
        return {"phase76_300394_known_url_text_extraction": {"ticker": "300394.SZ", "sources_checked": 0, "text_extraction_ok": 0, "texts_usable_for_evidence": 0, "rows": [], "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}
    from smr_phase76_known_url_breakthrough import load_candidates, verify_candidates
    candidates = verify_candidates(load_candidates("300394.SZ"))
    rows = []
    ok = 0
    for c in candidates:
        url = c.get("url", "")
        if not url or not c.get("verification_status", "").startswith("verified"):
            rows.append({"title": c.get("title", ""), "source_type": c.get("source_type", ""), "text_length": 0, "status": "not_verified"})
            continue
        er = extract_from_url(url, c.get("expected_content_type", "html"))
        er["title"] = c.get("title", "")
        er["source_type"] = c.get("source_type", "")
        er["allowed_usage"] = c.get("allowed_usage", "business_context")
        if er["status"] == "text_ok":
            ok += 1
        rows.append(er)
    usable = sum(1 for r in rows if r.get("quality_grade", "").startswith("usable"))
    return {"phase76_300394_known_url_text_extraction": {
        "ticker": "300394.SZ", "sources_checked": len(rows),
        "text_extraction_attempted": sum(1 for r in rows if r["status"] != "not_verified"),
        "text_extraction_ok": ok, "texts_usable_for_evidence": usable,
        "rows": rows, "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False
    }}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    mode = "dry_run" if getattr(a, "dry_run") else "execute"
    r = run(mode)
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
