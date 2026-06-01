import argparse,json,sys,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase111_config import load_config
from smr_phase111_owner_mode_domain_registry import build_owner_mode_domain_registry
from smr_phase111_owner_identity import build_owner_identity
from smr_phase111_owner_confirmation_gate import build_owner_confirmation_gate
from smr_phase111_research_risk_gate import build_research_risk_gate
from smr_phase111_paper_execution_deprecation_map import build_paper_execution_deprecation_map
from smr_phase111_cannot_conclude_guard import run_owner_mode_cannot_conclude_guard
from smr_phase111_backlog_reframe import build_backlog_reframe
def main():
    cfg=load_config();dom=build_owner_mode_domain_registry();ident=build_owner_identity()
    gate=build_owner_confirmation_gate();risk=build_research_risk_gate()
    pe=build_paper_execution_deprecation_map();guard=run_owner_mode_cannot_conclude_guard()
    bl=build_backlog_reframe()
    summary={"phase":"phase111","generated_at":datetime.now().isoformat(),"personal_use_system":cfg["personal_use"]["personal_use_system"],"owner_mode_enabled":cfg["personal_use"]["owner_mode_enabled"],"multi_user_assignment_required":cfg["multi_user"]["multi_user_assignment_required"],"owner_confirmation_required":cfg["owner_confirmation"]["owner_confirmation_required"],"paper_execution_enabled":False,"live_trading_enabled":False,"active_domains":dom["phase111_owner_mode_domain_registry"]["active_domains"],"deprecated_domains":dom["phase111_owner_mode_domain_registry"]["deprecated_domains"],"owner_identity":"single_personal_user","confirmation_gate_pass":gate["phase111_owner_confirmation_gate"]["all_pass"],"risk_gate_pass":risk["phase111_research_risk_gate"]["all_pass"],"paper_execution_fully_deprecated":pe["phase111_paper_execution_deprecation_map"]["all_permanently_disabled"],"guard":guard["phase111_guard"]["overall"],"violations":guard["phase111_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":"phase112_opportunity_radar_v1","paper_order_created":0,"paper_trade_created":0,"paper_position_created":0,"paper_pnl_calculated":0,"target_price_created":0,"position_sizing_created":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}
    out={"summary":summary}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
