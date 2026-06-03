import json, sys, os, argparse
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build_markdown():
    from build_phase153_onboarding_review_board import build as build_board
    board = build_board()["phase153_onboarding_review_board"]
    js = board["judge_summary"]
    lines = ["# Candidate Onboarding Review Brief", "",
        "## Judge Decisions", f"- Total candidates: {board['candidates_reviewed']}",
        f"- Ready for owner approval: {js.get('ready_for_owner_approval', 0)}",
        f"- Needs evidence follow-up: {js.get('needs_evidence_agent_follow_up', 0)}",
        f"- Needs identity confirmation: {js.get('needs_identity_confirmation', 0)}",
        f"- Blocked for now: {js.get('blocked_for_now', 0)}", "",
        "## Key Principles",
        "- Onboarding review is NOT watchlist activation.",
        "- Judge pass is NOT investment approval.",
        "- Owner approval is NOT trade approval.",
        "- Route ready is NOT data loaded. Financial/valuation routes are confirmed paths, not computed values.",
        "- Thesis seeds are unconfirmed. No customer/order data has been verified.",
        "- 300394 CNINFO blocker retained. 688041 derived valuation retained.",
        "- Candidates remain in Discovery Queue; no automatic Watch/Core promotion.",
    ]
    return "\n".join(lines)

def build_json():
    return {"phase153_onboarding_review_brief": {"brief_generated": True,
        "onboarding_is_research_only": True, "mock_used": False, "fixture_used": False}}

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args()
    if a.markdown: print(build_markdown())
    else: print(json.dumps(build_json(), indent=2, ensure_ascii=False, default=str))
