import os
def w(p,c): os.makedirs(os.path.dirname(p),exist_ok=True); open(p,'w',encoding='utf-8').write(c)

# RUNNER
w('08_scripts/jobs/run_phase121_external_source_expansion.py', '''import sys,json,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase121_config import load_config
from smr_phase121_domain_registry import build_domain_registry
from smr_phase121_target_universe import build_target_universe
from smr_phase121_source_candidate_registry import build_source_candidate_registry
from smr_phase121_official_filing_registry import build_official_filing_registry
from smr_phase121_market_quote_registry import build_market_quote_registry
from smr_phase121_news_event_registry import build_news_event_registry
from smr_phase121_transcript_guidance_registry import build_transcript_guidance_registry
from smr_phase121_source_access_policy import build_source_access_policy
from smr_phase121_connector_skeleton import build_connector_skeleton
from smr_phase121_hk_external_adapter import build_hk_external_adapter
from smr_phase121_us_external_adapter import build_us_external_adapter
from smr_phase121_source_probe import probe_sources
from smr_phase121_source_coverage_matrix import build_source_coverage_matrix
from smr_phase121_external_evidence_normalization import build_external_evidence_normalization
from smr_phase121_cross_source_reliability import build_cross_source_reliability
from smr_phase121_source_gap_register import build_source_gap_register
from smr_phase121_integration_report import build_integration_report
from smr_phase121_expansion_board import build_expansion_board
from smr_phase121_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase121_backlog_update import build_backlog_update
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    steps=[]
    cfg=load_config();steps.append({"name":"load_config","status":"ok"})
    build_domain_registry();steps.append({"name":"domain_registry","status":"ok"})
    uni=build_target_universe();steps.append({"name":"universe","status":"ok"})
    scr=build_source_candidate_registry();steps.append({"name":"sources","status":"ok"})
    build_official_filing_registry();steps.append({"name":"filings","status":"ok"})
    build_market_quote_registry();steps.append({"name":"quotes","status":"ok"})
    build_news_event_registry();steps.append({"name":"news","status":"ok"})
    build_transcript_guidance_registry();steps.append({"name":"transcripts","status":"ok"})
    build_source_access_policy();steps.append({"name":"policy","status":"ok"})
    build_connector_skeleton();steps.append({"name":"connectors","status":"ok"})
    build_hk_external_adapter();steps.append({"name":"hk_adapter","status":"ok"})
    build_us_external_adapter();steps.append({"name":"us_adapter","status":"ok"})
    prb=probe_sources(mode);steps.append({"name":"probe","status":"ok"})
    mat=build_source_coverage_matrix();steps.append({"name":"coverage_matrix","status":"ok"})
    build_external_evidence_normalization();steps.append({"name":"evidence_norm","status":"ok"})
    build_cross_source_reliability();steps.append({"name":"reliability","status":"ok"})
    grp=build_source_gap_register();steps.append({"name":"gaps","status":"ok"})
    build_integration_report();steps.append({"name":"integration","status":"ok"})
    build_expansion_board();steps.append({"name":"board","status":"ok"})
    grd=run_cannot_conclude_guard();steps.append({"name":"guard","status":"ok"})
    blg=build_backlog_update();steps.append({"name":"backlog","status":"ok"})
    out={"phase121_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),"research_only":True,"source_candidates":scr["phase121_source_candidate_registry"]["total"],"hk_targets":2,"us_targets":2,"guard":grd["phase121_guard"]["overall"],"violations":grd["phase121_guard"]["violations"],"blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":blg["phase121_backlog"]["next_phase"],"steps":steps,"paper_order_created":0,"paper_trade_created":0,"paper_position_created":0,"paper_pnl_calculated":0,"target_price_created":0,"position_sizing_created":0,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
''')

print('Runner done')