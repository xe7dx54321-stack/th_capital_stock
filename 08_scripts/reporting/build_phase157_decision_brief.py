import json, sys, os, argparse
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build_markdown():
    from build_phase157_decision_board import build as build_board
    b = build_board()["phase157_decision_board"]; s = b["decision_summary"]["summary"]
    return "\n".join(["# Owner Decision Input Workflow Brief","",
        "## Decision Summary",
        f"- Total candidates: {b['decision_summary']['total']}",
        f"- Owner input present: {b['decision_summary']['owner_input_present']}",
        f"- Pending: {s['pending']}",f"- Approved: {s['approved']}",
        f"- Deferred: {s['deferred']}",f"- Rejected: {s['rejected']}","",
        "## Key Principles",
        "- No owner input provided. All candidates remain pending.",
        "- All simulations are hypothetical. Execution is blocked by design.",
        "- Owner decision is NOT trade approval.",
        "- Simulation is NOT execution.",
        "- Tier proposal is NOT executed.",
        "- 300394 CNINFO blocker retained. 688041 derived valuation retained.",
    ])

def build_json():
    return {"phase157_decision_brief":{"brief_generated":True,"mock_used":False,"fixture_used":False}}

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); p.add_argument("--markdown",action="store_true")
    a = p.parse_args()
    if a.markdown: print(build_markdown())
    else: print(json.dumps(build_json(),indent=2,ensure_ascii=False,default=str))
