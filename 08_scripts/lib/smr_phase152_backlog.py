def build_phase152_backlog(bucket_result):
    buckets = bucket_result.get("buckets", {})
    entries = []
    for bucket, candidates in buckets.items():
        for c in candidates:
            entries.append({"ticker": c["ticker"], "name": c.get("name", ""),
                           "composite_score": c["composite_score"], "admission_bucket": bucket,
                           "status": "admission_scored"})
    return {"phase152_backlog": {"entries": len(entries), "backlog": entries, "mock_used": False, "fixture_used": False}}
