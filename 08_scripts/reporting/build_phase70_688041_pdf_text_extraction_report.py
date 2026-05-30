#!/usr/bin/env python3
"""Phase 70: 688041.SH PDF text extraction report."""
import argparse, json, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))

def build():
    from run_phase70_688041_pdf_text_extraction_hardening import run
    return run(mode="execute")

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        d = r["phase70_688041_pdf_text_extraction"]
        lines = ["# 688041.SH PDF Text Extraction", "",
                 f"- PDFs checked: {d['pdfs_checked']}",
                 f"- Text OK: {d['pdf_text_ok']}",
                 f"- Text failed: {d['pdf_text_failed']}",
                 f"- Usable for evidence: {d['texts_usable_for_evidence']}"]
        print("\n".join(lines))
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
