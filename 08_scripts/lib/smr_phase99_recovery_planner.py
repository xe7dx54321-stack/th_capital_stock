import json,os
from datetime import datetime
def build_recovery_plan(alert_mapper_result, fallback_selector):
    actions=alert_mapper_result.get("phase99_alert_to_recovery_mapper",{}).get("actions",[])
    plans=[]
    for a in actions:
        ra=a.get("recovery_action","monitor_only")
        plan={"source":a["source"],"alert_id":a["alert_id"],"recovery_action":ra,"priority":a["priority"],"status":"planned","planned_at":datetime.now().isoformat()[:10]}
        plans.append(plan)
    return {"phase99_recovery_planner":{"recovery_plans_created":len(plans),"plans":plans,"mock_used":False,"fixture_used":False}}
