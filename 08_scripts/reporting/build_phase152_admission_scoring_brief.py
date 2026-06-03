import json, sys, os, argparse
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build_markdown():
    from build_phase152_admission_scoring_board import build as build_board
    board = build_board()["phase152_admission_scoring_board"]
    buckets = board["buckets"]
    lines = [
        "# Candidate Admission Scoring Brief",
        "",
        "## Summary",
        f"- Candidates scored: {board['scored_candidates']}",
        f"- Admit to onboarding review: {buckets.get('admit_to_onboarding_review', 0)}",
        f"- Watch for more evidence: {buckets.get('watch_for_more_evidence', 0)}",
        f"- Manual identity/source review: {buckets.get('manual_identity_or_source_review', 0)}",
        f"- Defer: {buckets.get('defer', 0)}",
        f"- Reject for now: {buckets.get('reject_for_now', 0)}",
        "",
        "## Admission Scoring is Research-Only",
        "- Admission score is NOT an investment rating.",
        "- Admission bucket is NOT a buy/sell recommendation.",
        "- Admit to onboarding review does NOT mean buy.",
        "- Reject for now does NOT mean sell.",
        "- Candidates are NOT automatically added to Watch or Core.",
        "",
        "## Key Limitations",
        "- All scores are heuristic, not model-driven.",
        "- Cannot-conclude items are research caveats, not failures.",
        "- Owner review is required before any candidate moves to Watch.",
        "- 300394 CNINFO blocker and 688041 derived valuation label are preserved.",
    ]
    return "\n".join(lines)

def build_json():
    return {"phase152_admission_scoring_brief": {
        "brief_generated": True, "admission_is_research_only": True,
        "admission_not_investment_advice": True, "mock_used": False, "fixture_used": False}}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true")
    p.add_argument("--markdown", action="store_true")
    a = p.parse_args()
    if a.markdown: print(build_markdown())
    else: print(json.dumps(build_json(), indent=2, ensure_ascii=False, default=str))
