#!/usr/bin/env python3
import argparse, json, sys, uuid, datetime

def run(mode="execute", evidence_rows=None):
    if evidence_rows is None:
        evidence_rows = []
    if mode == "dry_run":
        return {"phase76_evidence_memory_report": {"records_written_total": 0, "mode": "dry_run", "rows": [], "memory_path_ignored": True, "mock_used": False, "fixture_used": False}}
    records = []
    for row in evidence_rows:
        records.append({
            "evidence_id": str(uuid.uuid4())[:8],
            "written_at": datetime.datetime.now().isoformat(),
            "ticker": row.get("ticker", ""),
            "source_type": row.get("source_type", ""),
            "business_variable": row.get("business_variable", ""),
            "evidence_strength": row.get("evidence_strength", ""),
            "claim_type": row.get("claim_type", ""),
            "limitation": row.get("limitation", ""),
            "cannot_conclude": row.get("cannot_conclude", [])
        })
    return {"phase76_evidence_memory_report": {"records_written_total": len(records), "rows": records, "memory_path_ignored": True, "mock_used": False, "fixture_used": False}}

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
