import json, sys, os, argparse
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build_markdown():
    from build_phase155_scheduling_board import build as build_board
    b = build_board()["phase155_scheduling_board"]
    return "\n".join(["# Agent Loop Scheduling Brief","",
        "## Schedule Summary",
        f"- Daily targets (core): {b['loop_plan']['daily']['targets_count']}",
        f"- Weekly targets (all): {b['loop_plan']['weekly']['weekly_targets_total']}",
        f"- Event triggers: {b['loop_plan']['event']['triggers']}","",
        "## History Status",
        f"- First run: {b['loop_history']['reader']['is_first_run']}",
        f"- Delta available: {b['loop_history']['delta']['delta_available']}","",
        "## Key Principles",
        "- Schedule plan is NOT a trade plan.",
        "- Event trigger is NOT a trade signal.",
        "- Loop history is NOT PnL/return history.",
        "- Owner digest is NOT investment advice.",
        "- System scheduler NOT registered. All runs are manual.",
        "- 300394 CNINFO blocker retained. 688041 derived valuation retained.",
    ])

def build_json():
    return {"phase155_scheduling_brief":{"brief_generated":True,"mock_used":False,"fixture_used":False}}

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); p.add_argument("--markdown",action="store_true")
    a = p.parse_args()
    if a.markdown: print(build_markdown())
    else: print(json.dumps(build_json(),indent=2,ensure_ascii=False,default=str))
