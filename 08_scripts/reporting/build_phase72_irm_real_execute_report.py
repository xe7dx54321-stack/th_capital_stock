#!/usr/bin/env python3
"""Phase 72 IRM real execute report."""
import argparse, json, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))
def build():
    from run_phase72_irm_real_execute import run
    return run(mode="execute")
def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build(); d = r["phase72_irm_real_execute"]
    if a.markdown:
        lines = ["# IRM Real Execute", "", f"QA found: {d['qa_items_found']}", f"Text available: {d['qa_text_available']}", f"Usable: {d['qa_text_usable']}"]
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()
