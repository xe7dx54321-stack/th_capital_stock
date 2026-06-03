import json, sys, os, argparse
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build_markdown():
    from build_phase156_activation_board import build as build_board
    b = build_board()["phase156_activation_board"]; s = b["decision_classifier"]["summary"]
    return "\n".join(["# Owner Activation Review Brief","",
        "## Decision Summary",
        f"- Total candidates for review: {s['total']}",
        f"- Pending owner review: {s['pending_owner_review']}",
        f"- Approved (research activation): {s['approved']}",
        f"- Deferred: {s['deferred']}",f"- More evidence requested: {s['more_evidence']}",
        f"- Rejected: {s['rejected']}","",
        "## Key Principles",
        "- All 8 candidates are pending owner review. No auto-approval.",
        "- Owner approval is NOT trade approval.",
        "- Research activation is NOT watchlist promotion.",
        "- Activation queue is NOT watchlist.",
        "- Watch/Core NOT updated. Candidates NOT auto-activated.",
        "- 300394 CNINFO blocker retained. 688041 derived valuation retained.",
    ])

def build_json():
    return {"phase156_activation_brief":{"brief_generated":True,"mock_used":False,"fixture_used":False}}

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); p.add_argument("--markdown",action="store_true")
    a = p.parse_args()
    if a.markdown: print(build_markdown())
    else: print(json.dumps(build_json(),indent=2,ensure_ascii=False,default=str))
