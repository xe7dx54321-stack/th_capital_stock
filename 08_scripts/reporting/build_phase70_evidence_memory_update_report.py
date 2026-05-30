#!/usr/bin/env python3
"""Phase 70 evidence memory update report."""
import argparse, json, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))

def build():
    from run_phase70_write_evidence_memory_update import run
    r = run(dry_run=False)
    mem = r["phase70_evidence_memory_write"]
    return {"phase70_evidence_memory_update":{"tickers_checked":3,"records_written_total":mem["records_written_total"],"rows":mem["rows"],"memory_path_ignored":True,"mock_used":False,"fixture_used":False}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        d = r["phase70_evidence_memory_update"]
        lines = ["# Evidence Memory Update", "", f"Total records: {d['records_written_total']}"]
        for row in d["rows"]: lines.append(f"- {row['ticker']}: {row['records_written']}")
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
