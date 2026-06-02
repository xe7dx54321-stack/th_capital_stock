import sys,json,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase122_config import load_config
from smr_phase122_domain_registry import build_domain_registry
from smr_phase122_load_phase117 import load_phase117_outputs
from smr_phase122_load_phase121 import load_phase121_outputs
from smr_phase122_load_phase116 import load_phase116_outputs
from smr_phase122_load_phase115 import load_phase115_outputs
from smr_phase122_load_phase114 import load_phase114_outputs
from smr_phase122_brief_aggregator import build_brief_aggregator
from smr_phase122_observed_first import build_observed_first
from smr_phase122_evidence_digest import build_evidence_digest
from smr_phase122_ticker_cards import build_ticker_cards
from smr_phase122_opportunity_section import build_opportunity_section
from smr_phase122_risk_gap_section import build_risk_gap_section
from smr_phase122_owner_actions import build_owner_actions
from smr_phase122_style_rules import load_style_rules
from smr_phase122_markdown_brief import build_markdown_brief
from smr_phase122_json_summary import build_json_summary
from smr_phase122_brief_lint import run_brief_lint
from smr_phase122_archive_writer import build_archive_writer
from smr_phase122_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase122_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"config","status":"ok"})
    build_domain_registry();steps.append({"name":"domain","status":"ok"})
    load_phase117_outputs();steps.append({"name":"load_p117","status":"ok"})
    load_phase121_outputs();steps.append({"name":"load_p121","status":"ok"})
    load_phase116_outputs();steps.append({"name":"load_p116","status":"ok"})
    load_phase115_outputs();steps.append({"name":"load_p115","status":"ok"})
    load_phase114_outputs();steps.append({"name":"load_p114","status":"ok"})
    build_brief_aggregator();steps.append({"name":"aggregator","status":"ok"})
    build_observed_first();steps.append({"name":"observed_first","status":"ok"})
    ev=build_evidence_digest();steps.append({"name":"evidence_digest","status":"ok"})
    cards=build_ticker_cards();steps.append({"name":"ticker_cards","status":"ok","detail":f"tickers={cards['phase122_ticker_cards']['total']}"})
    build_opportunity_section();steps.append({"name":"opportunity","status":"ok"})
    risk=build_risk_gap_section();steps.append({"name":"risk_gap","status":"ok"})
    owner=build_owner_actions();steps.append({"name":"owner_actions","status":"ok"})
    load_style_rules();steps.append({"name":"style_rules","status":"ok"})
    brief=build_markdown_brief();steps.append({"name":"brief","status":"ok","detail":f"lines={brief['phase122_markdown_brief']['lines']}"})
    build_json_summary();steps.append({"name":"json_summary","status":"ok"})
    lint=run_brief_lint();steps.append({"name":"lint","status":"ok","detail":lint["phase122_brief_lint"]["overall"]})
    build_archive_writer();steps.append({"name":"archive","status":"ok"})
    guard=run_cannot_conclude_guard();steps.append({"name":"guard","status":"ok","detail":guard["phase122_guard"]["overall"]})
    blg=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={"phase122_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),"research_only":True,"brief_generated":brief["phase122_markdown_brief"]["generated"],"brief_lint":lint["phase122_brief_lint"]["overall"],"brief_violations":lint["phase122_brief_lint"]["violations"],"guard":guard["phase122_guard"]["overall"],"guard_violations":guard["phase122_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"pending_network_sources":risk["phase122_risk_gap"]["pending_sources"],"next_phase":blg["phase122_backlog"]["next_phase"],"steps":steps,"trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,"paper_order_created":0,"paper_trade_created":0,"paper_position_created":0,"paper_pnl_calculated":0,"broker_api_called":False,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
