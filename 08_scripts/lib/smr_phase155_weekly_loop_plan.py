def build_weekly_loop_plan(loop_targets):
    all_t = loop_targets["all"]
    return {"phase155_weekly_loop_plan":{"schedule_type":"weekly","weekly_targets_total":len(all_t),"targets":all_t,"agents":["OpportunityAgent","EvidenceAgent","RiskAgent","ThesisAgent","DeepDiveAgent","BriefAgent","FeedbackAgent","JudgeAgent"],"run_day":"saturday","full_agent_battery":True,"schedule_is_not_trade_plan":True,"mock_used":False,"fixture_used":False}}
