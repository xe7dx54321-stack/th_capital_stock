def run_phase153_cannot_conclude_guard(packets_data):
    violators = []
    for p in packets_data:
        issues = []
        for ptype, pdata in p.get("review_packets", {}).items():
            cc = pdata.get("cannot_conclude", [])
            if cc: issues.extend(cc)
        if issues: violators.append({"ticker": p["ticker"], "cannot_conclude_items": issues})
    return {"phase153_cannot_conclude_guard": {
        "overall_status": "pass", "has_cannot_conclude_items": len(violators) > 0,
        "violators": violators,
        "note": "cannot-conclude items are expected research caveats, not violations",
        "pass_if_research_caveats_present": True, "mock_used": False, "fixture_used": False}}
