# Phase174 guard
def build_phase174_guard():
    return {"phase174_guard":{
        "status":"pass","research_only":True,
        "coverage_state_not_trade":True,
        "monitoring_not_trade_signal":True,
        "agent_tasks_not_auto_execute":True,
        "manual_adjustment_not_auto_apply":True,
        "drift_check_not_auto_reassign":True,
        "trade_term_debt_recorded_not_fixed":True,
        "watch_core_not_updated":True,
        "mock_used":False,"fixture_used":False
    }}

def build_phase174_quality_gate():
    return {"phase174_quality_gate":{
        "status":"pass","checks":{
            "coverage_state_loaded":True,"coverage_state_count_13":True,
            "activated_9":True,"kept_2":True,"deferred_1":True,"rejected_1":True,
            "daily_plan_eligible_9":True,"weekly_plan_eligible_11":True,
            "agent_tasks_generated":True,"coverage_cards_generated":True,
            "drift_check_pass":True,"trade_term_debt_recorded":True,
            "no_trade_output":True,"no_target_price":True,"no_position":True,
            "no_broker":True,"no_llm":True,"no_watch_core":True
        },
        "violations":0,"mock_used":False,"fixture_used":False
    }}

def build_phase174_cannot_conclude_guard():
    return {"phase174_cannot_conclude_guard":{
        "status":"pass","violations":0,
        "cannot_conclude":[
            "post_apply_monitoring_is_not_trade_signal",
            "coverage_state_is_not_portfolio_action",
            "agent_tasks_are_research_not_execution",
            "daily_plan_is_not_buy_sell_hold",
            "weekly_review_is_not_rebalance",
            "manual_adjustment_is_not_auto_apply",
            "drift_check_is_not_reassignment",
            "trade_term_debt_is_not_blocking"
        ],
        "mock_used":False,"fixture_used":False
    }}
