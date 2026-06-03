def build_daily_loop_plan(loop_targets):
    core = [t for t in loop_targets["all"] if t in loop_targets["core"]]
    return {"phase155_daily_loop_plan":{"schedule_type":"daily","targets_count":len(core),"targets":core,"agents":["OpportunityAgent","EvidenceAgent","RiskAgent","ThesisAgent","BriefAgent","JudgeAgent"],"run_window":"after_market_close","schedule_is_not_trade_plan":True,"mock_used":False,"fixture_used":False}}
