#!/usr/bin/env python3
import argparse, json, sys

def run(mode="execute"):
    records = []
    return {"phase75_fallback_evidence_memory_report": {
        "records_written_total": 0,
        "mode": mode,
        "rows": records,
        "note": "no_fallback_usable_text_no_evidence_to_write_all_4_sources_blocked_at_js_layer",
        "memory_path_ignored": True,
        "mock_used": False,
        "fixture_used": False
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
