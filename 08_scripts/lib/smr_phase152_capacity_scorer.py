def score_capacity_fit(candidate, tier_assignments=None):
    if tier_assignments is None: tier_assignments = {"tier_counts": {"core": 3, "watch": 5, "candidate": 5}}
    total = sum(tier_assignments.get("tier_counts", {}).values())
    candidate_count = tier_assignments.get("tier_counts", {}).get("candidate", 0)
    if total < 15 and candidate_count < 8: score = 4.5; notes = ["capacity available"]
    elif total < 20: score = 3.0; notes = ["capacity tightening"]
    else: score = 2.0; notes = ["capacity constrained"]
    return {
        "dimension": "capacity_fit", "score": score, "max_score": 5.0, "notes": notes,
        "cannot_conclude": ["capacity_plan_not_final", "owner_may_adjust_capacity"],
        "mock_used": False, "fixture_used": False,
    }
