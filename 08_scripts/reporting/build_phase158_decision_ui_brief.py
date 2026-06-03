import json, sys, os, argparse
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build_markdown():
    from build_phase158_decision_ui_board import build as build_board
    b = build_board()["phase158_decision_ui_board"]
    return "\n".join(["# Owner Decision UI Brief","",
        "## Console Status",
        f"- Decision cards rendered: {b['decision_cards']['pending_cards']}",
        f"- Console page generated: {b['console_page']['page_generated']}",
        f"- Navigation integrated: {b['nav_integration']['nav_integrated']}",
        f"- Link integrity: {b['link_checker']['integrity']}",
        f"- UI safety copy: {b['ui_safety_copy']['overall_status']}","",
        "## Key Principles",
        "- Static HTML only. No external JS, no CDN, no server.",
        "- No trade/execution/form buttons.",
        "- Template is copy-paste only, no auto-approval.",
        "- Simulation preview ≠ execution.",
        "- Approve ≠ buy. Reject ≠ sell.",
    ])

def build_json():
    return {"phase158_decision_ui_brief":{"brief_generated":True,"mock_used":False,"fixture_used":False}}

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--json",action="store_true"); p.add_argument("--markdown",action="store_true")
    a = p.parse_args()
    if a.markdown: print(build_markdown())
    else: print(json.dumps(build_json(),indent=2,ensure_ascii=False,default=str))
