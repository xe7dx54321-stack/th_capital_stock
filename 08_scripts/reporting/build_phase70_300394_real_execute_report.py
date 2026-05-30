#!/usr/bin/env python3
"""Phase 70: 300394.SZ real execute report."""
import argparse, json, sys
from pathlib import Path
J = Path(__file__).resolve().parents[1] / "jobs"
if str(J) not in sys.path: sys.path.insert(0, str(J))

def build():
    from run_phase70_300394_real_execute import run
    return run(mode="execute")

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        d = r["phase70_300394_real_execute"]
        lines = ["# 300394.SZ Real Execute", "",
                 f"- Identity found: {d['identity_found']}",
                 f"- Status: {d['overall_status']}"]
        if d.get("blocker"): lines.append(f"- Blocker: {d['blocker']}")
        print("\n".join(lines))
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
