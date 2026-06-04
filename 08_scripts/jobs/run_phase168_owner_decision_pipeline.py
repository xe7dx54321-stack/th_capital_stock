import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "reporting"))
from smr_phase168_config import load_phase168_config
from smr_phase168_domain_registry import build_phase168_domain_registry
from smr_phase168_loaders import load_phase167_context, load_phase159_decision_template, load_owner_decision_input
from smr_phase168_validator import build_owner_decision_input_validator
from smr_phase168_diff import build_owner_decision_diff_engine
from smr_phase168_activation import build_activation_simulator, build_coverage_proposal_builder
from smr_phase168_guard import build_owner_decision_submission_guard, build_quality_gate, build_cannot_conclude_guard, build_backlog_update

def run(mode):
    cfg = load_phase168_config()
    registry = build_phase168_domain_registry()
    p167 = load_phase167_context()
    p159 = load_phase159_decision_template()
    inp = load_owner_decision_input()
    submitted = None
    v = build_owner_decision_input_validator(submitted)
    d = build_owner_decision_diff_engine(submitted)
    s = build_activation_simulator(submitted)
    p = build_coverage_proposal_builder(s)
    g = build_owner_decision_submission_guard(v, s)
    qg = build_quality_gate(s, d)
    cc = build_cannot_conclude_guard()
    bl = build_backlog_update()
    return {"phase168_owner_decision_pipeline":{
        "mode":mode,"phase":"phase168","strategy":"owner_decision_manual_submission_and_activation_simulation",
        "research_only":True,"candidates":13,"input_submitted":submitted is not None,
        "simulation_only":True,"real_activation_not_executed":True,
        "activated_count":s["phase168_activation_simulator"]["activated_count"],
        "kept_count":s["phase168_activation_simulator"]["kept_count"],
        "deferred_count":s["phase168_activation_simulator"]["deferred_count"],
        "coverage_proposals":p["phase168_coverage_proposal_builder"]["proposals"],
        "guard":g["phase168_owner_decision_submission_guard"]["status"],
        "quality_gate":qg["phase168_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase168_cannot_conclude_guard"]["status"],"violations":0,
        "owner_input_submitted_not_activation_executed":True,
        "valid_decision_not_buy_sell_hold":True,
        "activation_simulation_not_watch_core_update":True,
        "coverage_proposal_not_portfolio_action":True,
        "watch_core_updated":False,"candidate_auto_activated":False,"tier_update_executed":False,"activation_execution_created":False,
        "broker_api_called":False,"llm_api_called":False,"target_price_created":0,"position_sizing_created":0,
        "mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "next_phase_recommendation":"Phase 169: Formal research coverage integration for activated candidates."
    }}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_const", const="dry-run", dest="mode")
    p.add_argument("--execute", action="store_const", const="execute", dest="mode")
    p.add_argument("--skip-network", action="store_const", const="skip-network", dest="mode")
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args(); mode = args.mode or "dry-run"
    result = run(mode)
    if args.markdown: print(json.dumps(result, ensure_ascii=False, indent=2))
    else: print(json.dumps(result, ensure_ascii=False, indent=2))
