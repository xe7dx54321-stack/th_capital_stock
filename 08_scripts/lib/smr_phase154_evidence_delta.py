def build_evidence_delta(targets):
    deltas = []
    for t in targets:
        deltas.append({"ticker": t, "new_evidence_found": False,
                       "evidence_gaps_remaining": ["customer_order_data","supplier_contracts"],
                       "cannot_conclude": ["no_new_source_access", "evidence_is_simulation"]})
    return {"phase154_evidence_delta": {"deltas": len(deltas), "evidence_deltas": deltas,
        "mock_used": False, "fixture_used": False}}
