#!/usr/bin/env python3
"""Phase 71 fallback evidence memory report."""
import argparse, json, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))

def build():
    from run_phase71_write_fallback_evidence_memory import run
    r = run(dry_run=False)
    mem = r["fallback_evidence_memory_write"]
    return {"fallback_evidence_memory_report": {"records_written_total": mem["records_written_total"], "rows": mem["rows"], "memory_path_ignored": True, "mock_used": False, "fixture_used": False}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        d = r["fallback_evidence_memory_report"]
        lines = ["# Fallback Evidence Memory", "", f"Total records: {d['records_written_total']}"]
        for row in d["rows"]: lines.append(f"- {row['ticker']}: {row['records_written']}")
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
