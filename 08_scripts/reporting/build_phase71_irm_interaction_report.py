#!/usr/bin/env python3
"""Phase 71 IRM interaction report."""
import argparse, json, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))

def build():
    from run_phase71_irm_interaction_fetch import run
    return run(mode="execute")

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        rep = r.get("irm_interaction_report", r)
        lines = ["# IRM Interaction Report"]
        for row in rep.get("rows", []): lines.append(f"- {row['ticker']}: {row.get('status','')} (QA items: {row.get('qa_items_found',0)})")
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
