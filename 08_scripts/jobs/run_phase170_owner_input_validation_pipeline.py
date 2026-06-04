import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "reporting"))
from smr_phase170_config import load_phase170_config
from smr_phase170_domain_registry import build_phase170_domain_registry
from smr_phase170_loaders import load_phase169b_context, load_phase168_context, try_read_owner_input
from smr_phase170_validator import validate_owner_input
from smr_phase170_state_preview import build_formal_research_state_preview, build_tier_proposal_preview, build_agent_task_delta, build_daily_monitoring_preview
from smr_phase170_guard import build_owner_input_submission_guard, build_quality_gate, build_cannot_conclude_guard, build_backlog_update

def run(mode):
    cfg = load_phase170_config()
    registry = build_phase170_domain_registry()
    p169 = load_phase169b_context()
    p168 = load_phase168_context()
    inp = try_read_owner_input()
    v = validate_owner_input(inp)
    s = build_formal_research_state_preview(v)
    t = build_tier_proposal_preview(v)
    a = build_agent_task_delta(v)
    d = build_daily_monitoring_preview(v)
    g = build_owner_input_submission_guard(v)
    qg = build_quality_gate(v, s)
    cc = build_cannot_conclude_guard()
    bl = build_backlog_update()
    return {"phase170_owner_input_validation_pipeline":{
        "mode":mode,"phase":"phase170","strategy":"owner_input_submission_validation_and_formal_research_state_preview",
        "research_only":True,"input_read":inp is not None,
        "validator_status":v["phase170_schema_validator"]["status"],
        "valid_entries":v["phase170_schema_validator"]["valid_entries"],
        "quarantined":v["phase170_schema_validator"]["quarantined_entries"],
        "missing":v["phase170_schema_validator"]["missing_entries"],
        "state_preview_generated":s["phase170_formal_research_state_preview"]["entries"]>0,
        "state_not_updated":s["phase170_formal_research_state_preview"]["state_not_updated"],
        "tier_proposals":t["phase170_tier_proposal_preview"]["entries"],
        "agent_tasks":a["phase170_agent_task_delta"]["entries"],
        "guard":g["phase170_owner_input_submission_guard"]["status"],
        "quality_gate":qg["phase170_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase170_cannot_conclude_guard"]["status"],"violations":qg["phase170_quality_gate"]["violations"],
        "validated_input_not_activation":True,"state_preview_not_update":True,
        "tier_proposal_not_assignment":True,"agent_tasks_not_execution":True,
        "watch_core_updated":False,"candidate_auto_activated":False,"tier_update_executed":False,"activation_execution_created":False,
        "target_price_created":0,"position_sizing_created":0,
        "mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "next_phase_recommendation":"Phase 171: Owner reviews state preview and confirms activation; system executes formal state update."
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
