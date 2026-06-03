def build_tier_proposal_diff(summary):
    approved = summary.get("approved",0)
    if approved > 0:
        diff = [{"change":"candidate_count_increase","delta":f"+{approved}","note":"If approved candidates activated, candidate tier would grow. This is a PROPOSAL ONLY, not executed."}]
    else:
        diff = [{"change":"no_change","delta":"0","note":"No candidates approved for activation. Tier unchanged."}]
    return {"phase157_tier_proposal_diff":{"diff_generated":True,"diffs":diff,"proposal_only_not_executed":True,"watch_core_updated":False,"tier_update_executed":False,"candidate_auto_activated":False,"mock_used":False,"fixture_used":False}}
