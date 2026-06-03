import json, sys, os, argparse
from pathlib import Path
from datetime import datetime
BASE_LIB = Path(__file__).resolve().parent.parent / "lib"
BASE_REPORTING = Path(__file__).resolve().parent.parent / "reporting"
sys.path.insert(0, str(BASE_LIB))
sys.path.insert(0, str(BASE_REPORTING))
from build_phase156_activation_dashboard import build

def run(mode="dry-run"):
    s = datetime.now().isoformat(); r = build(); d = r["phase156_activation_dashboard"]; b = d["board"]; dc = b["decision_classifier"]; cs = dc["summary"]
    return {"phase156_activation_review_pipeline":{"mode":mode,"started_at":s,"finished_at":datetime.now().isoformat(),
        "candidates_for_review":dc["total"],"pending_owner_review":cs["pending_owner_review"],
        "approved":cs["approved"],"deferred":cs["deferred"],"rejected":cs["rejected"],
        "quality_gate":d["quality_gate"]["overall_status"],"guard":d["guard"]["overall_status"],
        "cannot_conclude_guard":d["cannot_conclude_guard"]["overall_status"],"violations":d["guard"]["violations"],
        "research_only":True,"owner_decision_required":True,"auto_approval_allowed":False,
        "owner_approval_not_trade_approval":True,"approve_not_equal_to_buy":True,"reject_not_equal_to_sell":True,
        "activation_queue_not_watchlist":True,"watch_core_updated":False,"candidate_auto_activated":False,
        "mock_used":False,"fixture_used":False,
        "trade_recommendation_created":0,"target_price_created":0,"position_sizing_created":0,
        "paper_order_created":0,"paper_trade_created":0,"broker_api_called":False,"llm_api_called":False,
    }}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--dry-run",action="store_true"); p.add_argument("--execute",action="store_true")
    p.add_argument("--skip-network",action="store_true"); p.add_argument("--json",action="store_true")
    a = p.parse_args(); m = "execute" if a.execute else ("skip-network" if a.skip_network else "dry-run")
    print(json.dumps(run(m), indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__": main()
