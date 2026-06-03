def reject_invalid_decisions(validator_result):
    rejected = [r for r in validator_result.get("results",[]) if not r["decision_valid"] or not r["no_forbidden_terms"]]
    return {"phase157_invalid_rejector":{"invalid_count":len(rejected),"rejected":rejected,"rejection_reason":"decision_not_in_allowed_set_or_contains_trade_language","all_rejected_remain_pending":True,"mock_used":False,"fixture_used":False}}
