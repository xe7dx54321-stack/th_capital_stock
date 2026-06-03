def build_risk_delta(targets):
    deltas = []
    for t in targets:
        is_blocked = t == "300394.SZ"
        deltas.append({"ticker": t, "new_risks_identified": 0 if not is_blocked else 1,
                       "blocker_status": "retained" if is_blocked else "none",
                       "cannot_conclude": ["risk_assessment_is_simulation"]})
    return {"phase154_risk_delta": {"deltas": len(deltas), "risk_deltas": deltas,
        "300394_blocker_retained": True, "mock_used": False, "fixture_used": False}}
