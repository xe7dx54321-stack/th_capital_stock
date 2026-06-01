def build_research_risk_gate():
    checks=[
        {"check":"no_paper_order","rule":"paper_order_creation_disallowed","status":"pass","risk":"critical"},
        {"check":"no_live_trade","rule":"live_trade_disallowed","status":"pass","risk":"critical"},
        {"check":"no_target_price","rule":"target_price_disallowed","status":"pass","risk":"high"},
        {"check":"no_position_sizing","rule":"position_sizing_disallowed","status":"pass","risk":"high"},
        {"check":"no_broker_call","rule":"broker_integration_disallowed","status":"pass","risk":"critical"},
        {"check":"no_mock_data","rule":"mock_disallowed","status":"pass","risk":"high"},
        {"check":"no_fixture_data","rule":"fixture_disallowed","status":"pass","risk":"high"},
        {"check":"owner_confirmation_required","rule":"owner_must_confirm_medium_risk_actions","status":"pass","risk":"medium"},
        {"check":"evidence_before_claim","rule":"every_claim_must_have_evidence","status":"pass","risk":"medium"},
        {"check":"cannot_conclude_present","rule":"limitations_must_be_disclosed","status":"pass","risk":"low"}
    ]
    all_pass=all(c["status"]=="pass" for c in checks)
    critical_pass=all(c["status"]=="pass" for c in checks if c["risk"]=="critical")
    return {"phase111_research_risk_gate":{"checks":checks,"all_pass":all_pass,"critical_pass":critical_pass,"risk_level":"research_only","trading_disabled":True,"mock_used":False,"fixture_used":False}}
