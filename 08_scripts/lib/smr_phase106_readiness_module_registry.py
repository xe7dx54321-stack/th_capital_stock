import json,os
def build_readiness_module_registry():
    modules=[
        {"module_id":"phase102","name":"historical_replay","status":"addressed","blockers_resolved":True,"key_output":"backtest_missing=addressed","no_order":True,"no_trade":True},
        {"module_id":"phase103","name":"risk_control","status":"partially_addressed","blockers_resolved":False,"key_output":"risk_control_missing=partially_addressed","no_order":True,"no_trade":True},
        {"module_id":"phase104","name":"human_approval","status":"partially_addressed","blockers_resolved":False,"key_output":"human_approval_missing=partially_addressed","no_order":True,"no_trade":True},
        {"module_id":"phase105","name":"kill_switch","status":"partially_addressed","blockers_resolved":False,"key_output":"kill_switch_missing=partially_addressed","no_order":True,"no_trade":True}
    ]
    return {"phase106_readiness_module_registry":{"total_modules":len(modules),"modules":modules,"all_no_order":True,"all_no_trade":True,"mock_used":False,"fixture_used":False}}
