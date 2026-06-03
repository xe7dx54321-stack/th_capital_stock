def plan_admission_next_actions(bucket_result):
    buckets = bucket_result.get("buckets", {})
    bucket_actions = {
        "admit_to_onboarding_review": "move to onboarding review; prepare activation checklist; assign Evidence Agent",
        "watch_for_more_evidence": "keep in Discovery Queue; schedule re-score in 7 days",
        "manual_identity_or_source_review": "flag for owner manual review",
        "defer": "keep in backlog; revisit if capacity improves",
        "reject_for_now": "archive from active Discovery Queue; document reason",
    }
    actions = []
    for bucket, candidates in buckets.items():
        for c in candidates:
            actions.append({"ticker": c["ticker"], "name": c.get("name", ""), "admission_bucket": bucket,
                           "composite_score": c["composite_score"],
                           "next_action": bucket_actions.get(bucket, "manual review"),
                           "requires_owner_review": bucket in ("admit_to_onboarding_review", "manual_identity_or_source_review"),
                           "auto_add_to_watchlist": False, "auto_promote_to_core": False})
    return {"phase152_next_action_planner": {"actions_planned": len(actions), "next_actions": actions,
                                             "auto_activation_disabled": True, "owner_review_required": True,
                                             "mock_used": False, "fixture_used": False}}
