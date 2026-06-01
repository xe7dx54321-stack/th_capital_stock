def build_evidence_first_policy():
    rules=[
        {"rule":"every_claim_must_have_evidence","applies_to":"research_output","status":"enforced"},
        {"rule":"every_metric_must_have_source","applies_to":"financial_data","status":"enforced"},
        {"rule":"every_signal_must_have_period","applies_to":"time_series_signals","status":"enforced"},
        {"rule":"every_delta_must_have_baseline","applies_to":"delta_detection","status":"enforced"},
        {"rule":"every_anomaly_must_have_explanation","applies_to":"anomaly_flags","status":"enforced"},
        {"rule":"every_blocker_must_have_allowed_action","applies_to":"coverage_blockers","status":"enforced"},
        {"rule":"no_conclusion_without_evidence","applies_to":"internal_brief","status":"enforced"},
        {"rule":"cannot_conclude_must_be_disclosed","applies_to":"all_output","status":"enforced"}
    ]
    return {"phase111_evidence_first_policy":{"total_rules":len(rules),"all_enforced":all(r["status"]=="enforced" for r in rules),"rules":rules,"evidence_required_before_decision":True,"mock_used":False,"fixture_used":False}}
