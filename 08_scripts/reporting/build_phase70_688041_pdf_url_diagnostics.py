#!/usr/bin/env python3
"""Phase 70: 688041.SH PDF URL diagnostics report."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

def build():
    from smr_phase70_pdf_url_diagnostics import diagnose_pdf_urls
    return diagnose_pdf_urls()

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        diag = r["phase70_688041_pdf_url_diagnostics"]
        lines = ["# 688041.SH PDF URL Diagnostics", "",
                 f"- Metadata checked: {diag['metadata_sources_checked']}",
                 f"- PDF URLs found: {diag['pdf_urls_found']}",
                 f"- HEAD OK: {diag['pdf_urls_head_ok']}",
                 f"- PDF-like responses: {diag['pdf_like_response']}",
                 f"- Top failures: {', '.join(diag.get('top_failure_reasons',[]))}"]
        print("\n".join(lines))
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
