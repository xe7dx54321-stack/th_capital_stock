# Phase174 config loader
import json, os

def load_phase174_config():
    p = "config/phase174_post_apply_coverage_console.json"
    if not os.path.exists(p):
        return {"phase174_config":{"status":"config_missing","mock_used":False,"fixture_used":False}}
    with open(p,"r",encoding="utf-8-sig") as f:
        c = json.load(f)
    return {"phase174_config":{
        "status":"loaded","phase":"phase174","strategy":c["strategy"],
        "research_only":c["research_only"],
        "candidates_count":len(c.get("candidates",[])),
        "daily_monitoring":c.get("daily_monitoring_enabled",True),
        "weekly_review":c.get("weekly_review_enabled",True),
        "agent_task_queue":c.get("agent_task_queue_enabled",True),
        "drift_check":c.get("coverage_drift_check_enabled",True),
        "manual_adjustment":c.get("manual_adjustment_workflow_enabled",True),
        "trade_term_debt":c.get("trade_term_debt_recorded",True),
        "state_path_ignored":c.get("state_path_ignored",True),
        "mock_used":False,"fixture_used":False
    }}
