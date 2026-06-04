import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase170_loaders import try_read_owner_input
from smr_phase170_validator import validate_owner_input
from smr_phase170_state_preview import build_formal_research_state_preview, build_tier_proposal_preview, build_agent_task_delta, build_daily_monitoring_preview
from smr_phase170_guard import build_owner_input_submission_guard, build_quality_gate, build_cannot_conclude_guard

def build():
    inp = try_read_owner_input()
    v = validate_owner_input(inp)
    s = build_formal_research_state_preview(v)
    t = build_tier_proposal_preview(v)
    a = build_agent_task_delta(v)
    d = build_daily_monitoring_preview(v)
    g = build_owner_input_submission_guard(v)
    qg = build_quality_gate(v, s)
    cc = build_cannot_conclude_guard()
    return {"phase170_owner_input_validation_board":{
        "input_read":inp is not None,"validator_status":v["phase170_schema_validator"]["status"],
        "valid_entries":v["phase170_schema_validator"]["valid_entries"],
        "quarantined":v["phase170_schema_validator"]["quarantined_entries"],
        "missing":v["phase170_schema_validator"]["missing_entries"],
        "state_preview_entries":s["phase170_formal_research_state_preview"]["entries"],
        "tier_proposals":t["phase170_tier_proposal_preview"]["entries"],
        "agent_tasks":a["phase170_agent_task_delta"]["entries"],
        "state_not_updated":True,
        "guard":g["phase170_owner_input_submission_guard"]["status"],
        "quality_gate":qg["phase170_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase170_cannot_conclude_guard"]["status"],"violations":qg["phase170_quality_gate"]["violations"],
        "research_only":True,"watch_core_updated":False,
        "mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_created":0
    }}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args(); result = build()
    if args.markdown:
        for k,v in result["phase170_owner_input_validation_board"].items(): print(f"- {k}: {v}")
    else: print(json.dumps(result, ensure_ascii=False, indent=2))
