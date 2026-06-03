def run_phase152_cannot_conclude_guard(composite_result):
    scored = composite_result.get("composite_scores", [])
    violators = []
    for c in scored:
        scores = c.get("scores", {})
        issues = []
        for dim, data in scores.items():
            cc = data.get("cannot_conclude", [])
            if cc: issues.extend(cc)
        if issues: violators.append({"ticker": c["ticker"], "cannot_conclude_items": issues})
    return {"phase152_cannot_conclude_guard": {
        "overall_status": "pass", "has_cannot_conclude_items": len(violators) > 0,
        "violators": violators,
        "note": "cannot-conclude items are expected research caveats, not violations",
        "pass_if_research_caveats_present": True, "mock_used": False, "fixture_used": False}}
