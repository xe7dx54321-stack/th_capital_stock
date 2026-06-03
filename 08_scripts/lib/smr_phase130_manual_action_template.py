import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase130_manual_url_template import build_manual_url_template
from smr_phase130_gap_closeout_report import build_gap_closeout_report

def build_manual_action_template():
    url_templates=build_manual_url_template()["phase130_manual_url_template"]["templates"]
    closeout=build_gap_closeout_report()["phase130_gap_closeout_report"]
    return {"phase130_manual_action_template":{"ticker":"300394.SZ","owner_checklist":[{"step":1,"action":"Try visiting SZSE company page to verify disclosure availability","url":"https://www.szse.cn/certificate/individual/index.html?code=300394","priority":"high"},{"step":2,"action":"Try visiting Eastmoney financial data page to verify data completeness","url":"https://emweb.securities.eastmoney.com/pc_hsf10/pages/index.html?type=web&code=300394","priority":"high"},{"step":3,"action":"Optionally search CNINFO for org_id by visiting any 300394 disclosure page and copying orgId from URL","url":"https://www.cninfo.com.cn/new/disclosure/stock?stockCode=300394&orgId=","priority":"medium"},{"step":4,"action":"Check company IR website for financial reports","url":"https://www.tfc-sz.com","priority":"low"},{"step":5,"action":"Report findings: which sources work, whether org_id was found","priority":"required"}],"url_templates":url_templates,"resolution_status":closeout["blocker_status"],"all_require_owner_action":True,"mock_used":False,"fixture_used":False}}
