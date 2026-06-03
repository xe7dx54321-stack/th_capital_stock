def classify_admission_buckets(composite_result):
    scored = composite_result.get("composite_scores", [])
    buckets = {"admit_to_onboarding_review": [], "watch_for_more_evidence": [],
               "manual_identity_or_source_review": [], "defer": [], "reject_for_now": []}
    bucket_defs = [("admit_to_onboarding_review", 3.5, 5.0), ("watch_for_more_evidence", 2.5, 3.5),
                   ("manual_identity_or_source_review", 1.5, 2.5), ("defer", 0.5, 1.5), ("reject_for_now", 0.0, 0.5)]
    for c in scored:
        s = c["composite_score"]
        for bucket, lo, hi in bucket_defs:
            if s >= lo and s < hi: buckets[bucket].append(c); break
        else: buckets["reject_for_now"].append(c)
    summary = {k: len(v) for k, v in buckets.items()}
    return {"phase152_bucket_classifier": {"buckets": buckets, "summary": summary, "total_classified": len(scored),
                                           "admission_bucket_not_investment_rating": True,
                                           "mock_used": False, "fixture_used": False}}
