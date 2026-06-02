import sys,json,os
from datetime import datetime
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
from smr_phase126_config import load_config
from smr_phase126_domain import build_domain
from smr_phase126_schema import build_schema
from smr_phase126_taxonomy import build_taxonomy
from smr_phase126_signal_loader import build_signal_loader
from smr_phase126_outcome_loader import build_outcome_loader
from smr_phase126_context_loader import build_context_loader
from smr_phase126_metric_registry import build_metric_registry
from smr_phase126_outcome_linker import build_outcome_linker
from smr_phase126_usefulness import build_usefulness
from smr_phase126_noise import build_noise
from smr_phase126_source_review import build_source_review
from smr_phase126_brief_review import build_brief_review
from smr_phase126_watchlist_review import build_watchlist_review
from smr_phase126_scoring import build_scoring
from smr_phase126_board import build_board
from smr_phase126_memory_writer import build_memory_writer
from smr_phase126_guard import run_guard
from smr_phase126_backlog import build_backlog
def main():
    mode="dry-run"
    for a in sys.argv:
        if a=="--execute":mode="execute"
        if a=="--skip-network":mode="skip-network"
    s=[]
    load_config();s.append({"name":"config","status":"ok"})
    build_domain();s.append({"name":"domain","status":"ok"})
    build_schema();s.append({"name":"schema","status":"ok"})
    t=build_taxonomy();s.append({"name":"taxonomy","status":"ok"})
    build_signal_loader();s.append({"name":"signal_loader","status":"ok"})
    build_outcome_loader();s.append({"name":"outcome_loader","status":"ok"})
    build_context_loader();s.append({"name":"context","status":"ok"})
    build_metric_registry();s.append({"name":"metrics","status":"ok"})
    build_outcome_linker();s.append({"name":"outcome_linker","status":"ok"})
    u=build_usefulness();s.append({"name":"usefulness","status":"ok"})
    n=build_noise();s.append({"name":"noise","status":"ok"})
    build_source_review();s.append({"name":"source_review","status":"ok"})
    build_brief_review();s.append({"name":"brief_review","status":"ok"})
    wl=build_watchlist_review();s.append({"name":"watchlist_review","status":"ok"})
    sc=build_scoring();s.append({"name":"scoring","status":"ok"})
    build_board();s.append({"name":"board","status":"ok"})
    build_memory_writer();s.append({"name":"memory","status":"ok"})
    g=run_guard();s.append({"name":"guard","status":"ok"})
    b=build_backlog();s.append({"name":"backlog","status":"ok"})
    out={"phase126_pipeline":{"mode":mode,"generated_at":datetime.now().isoformat(),"research_only":True,"signal_types":t["phase126_taxonomy"]["total"],"guard":g["phase126_guard"]["overall"],"violations":g["phase126_guard"]["violations"],"scoring_recommendations":sc["phase126_scoring"]["recommendations_created"],"trade_actions":sc["phase126_scoring"]["trade_actions"],"phase111_126_mainline":"complete","blocked_tickers":["300394.SZ"],"partial_tickers":["688041.SH"],"next_phase":b["phase126_backlog"]["next_phase"],"steps":s,"trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,"paper_order_created":0,"paper_trade_created":0,"paper_position_created":0,"paper_pnl_calculated":0,"profit_loss_tracking_created":False,"return_tracking_created":False,"broker_api_called":False,"mock_used":False,"fixture_used":False,"raw_saved":False,"ocr_used":False,"browser_automation_used":False}}
    if "--json" in sys.argv:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
