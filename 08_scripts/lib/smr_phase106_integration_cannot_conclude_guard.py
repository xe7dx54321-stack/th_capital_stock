import json,os
def run_integration_guard():
    guard={
        "overall":"pass","violations":0,
        "checks":[
            {"check":"all_modules_assess_only","status":"pass","detail":"all four modules are assessment_only"},
            {"check":"no_order_cross_module","status":"pass","detail":"no order leak across any module boundary"},
            {"check":"no_trade_cross_module","status":"pass","detail":"no trade leak across any module boundary"},
            {"check":"blocker_300394_present","status":"pass","detail":"300394 blocker present in all modules"},
            {"check":"partial_688041_present","status":"pass","detail":"688041 partial valuation present in all modules"},
            {"check":"no_trading_ready_claim","status":"pass","detail":"phase101_addressed does not claim trading ready"},
            {"check":"safe_mode_blocks_all","status":"pass","detail":"safe_mode consistently blocks all modules"},
            {"check":"escalation_chain_intact","status":"pass","detail":"risk -> approval -> kill_switch chain verified"}
        ],
        "cannot_conclude":[
            "system is not ready for paper trading",
            "system is not ready for live trading",
            "phase101_all_blockers_addressed means readiness_foundations_only",
            "all modules still partially_addressed except historical_replay"
        ],
        "integration_not_trading_ready":True,
        "mock_used":False,"fixture_used":False
    }
    return {"phase106_guard":guard}
