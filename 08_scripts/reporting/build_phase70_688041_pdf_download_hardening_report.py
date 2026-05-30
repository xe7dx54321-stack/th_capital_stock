#!/usr/bin/env python3
"""Phase 70: 688041.SH PDF download hardening report."""
import argparse, json, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))

def build():
    from run_phase70_688041_pdf_download_hardening import run
    return run(mode="execute")

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        d = r["phase70_688041_pdf_download_hardening"]
        lines = ["# 688041.SH PDF Download Hardening", "",
                 f"- Selected: {d['pdfs_selected']}",
                 f"- Download OK: {d['pdf_download_ok']}",
                 f"- Download Failed: {d['pdf_download_failed']}"]
        print("\n".join(lines))
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
