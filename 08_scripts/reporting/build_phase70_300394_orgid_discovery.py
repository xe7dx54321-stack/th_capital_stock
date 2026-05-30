#!/usr/bin/env python3
"""Phase 70: 300394.SZ org_id discovery report."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

def build():
    from smr_phase70_cninfo_orgid_discovery import discover_org_id
    return discover_org_id()

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        d = r["phase70_300394_orgid_discovery"]
        lines = ["# 300394.SZ Org ID Discovery", "",
                 f"- Candidates tested: {d['candidates_tested']}",
                 f"- Verified found: {d['verified_org_id_found']}"]
        if d.get("org_id"): lines.append(f"- Org ID: {d['org_id']}")
        if not d["verified_org_id_found"]: lines.append(f"- Failure: {d.get('failure_reason','')}")
        print("\n".join(lines))
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
