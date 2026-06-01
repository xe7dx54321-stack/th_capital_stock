import json,os,sys
def load_all_phase_status():
    sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
    statuses={}
    try:
        from smr_phase102_backlog_update import build_backlog_update as p102_bl
        bl=p102_bl()
        statuses["phase102"]={"backtest_missing":"addressed","pnl_backtest_allowed":False}
    except: statuses["phase102"]={"status":"unavailable"}
    try:
        from smr_phase103_config import is_live_risk_enabled
        statuses["phase103"]={"risk_control_missing":"partially_addressed","live_risk_execution_enabled":is_live_risk_enabled()}
    except: statuses["phase103"]={"status":"unavailable"}
    try:
        from smr_phase104_config import is_assessment_only as p104_ao
        statuses["phase104"]={"human_approval_missing":"partially_addressed","assessment_only":p104_ao()}
    except: statuses["phase104"]={"status":"unavailable"}
    try:
        from smr_phase105_config import is_assessment_only as p105_ao
        statuses["phase105"]={"kill_switch_missing":"partially_addressed","assessment_only":p105_ao()}
    except: statuses["phase105"]={"status":"unavailable"}
    return {"phase106_phase_status_loader":{"phases_loaded":len(statuses),"statuses":statuses,"mock_used":False,"fixture_used":False}}
