import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "reporting"))
from smr_phase172_config import load_phase172_config
from smr_phase170_validator import validate_owner_input
from smr_phase170_loaders import try_read_owner_input
from smr_phase171_core import build_apply_confirmation_gate, build_coverage_apply_package
from smr_phase172_core import build_prerequisite_checker, build_execute_apply_gate, build_coverage_state_executor, build_post_apply_verifier
from smr_phase172_guard import build_formal_coverage_apply_guard, build_quality_gate, build_cannot_conclude_guard, build_backlog_update

def run(mode, execute_apply=False):
    cfg = load_phase172_config()
    inp = try_read_owner_input()
    v = validate_owner_input(inp)
    cg = build_apply_confirmation_gate(v)
    ap = build_coverage_apply_package(v)
    pr = build_prerequisite_checker(inp, v, cg, ap)
    eg = build_execute_apply_gate(pr, execute_apply)
    ex = build_coverage_state_executor(pr, execute_apply)
    pv = build_post_apply_verifier(ex)
    g = build_formal_coverage_apply_guard(ex)
    qg = build_quality_gate(pr, ex)
    cc = build_cannot_conclude_guard()
    bl = build_backlog_update(ex["phase172_coverage_state_executor"]["executed"])
    return {"phase172_coverage_apply_pipeline":{
        "mode":mode,"phase":"phase172","strategy":"formal_research_coverage_state_apply_execution_gate",
        "research_only":True,"input_read":inp is not None,
        "prerequisites_met":pr["phase172_prerequisite_checker"]["all_prerequisites_met"],
        "execute_apply_flag":execute_apply,"can_execute":eg["phase172_execute_apply_gate"]["can_execute"],
        "applied":ex["phase172_coverage_state_executor"]["executed"],
        "candidates_updated":ex["phase172_coverage_state_executor"]["candidates_updated"],
        "coverage_state_only":True,"trade_state_not_updated":True,"watch_core_not_updated":True,
        "state_path_ignored":ex["phase172_coverage_state_executor"]["state_path_ignored"],
        "guard":g["phase172_formal_coverage_apply_guard"]["status"],
        "quality_gate":qg["phase172_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase172_cannot_conclude_guard"]["status"],"violations":0,
        "coverage_apply_is_not_trade":True,"research_state_is_not_portfolio_action":True,
        "target_price_created":0,"position_sizing_created":0,"broker_api_called":False,
        "mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "next_phase_recommendation":"Phase 173: With formal coverage state applied, integrate activated candidates into daily monitoring and research pipeline."
    }}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_const", const="dry-run", dest="mode")
    p.add_argument("--execute", action="store_const", const="execute", dest="mode")
    p.add_argument("--skip-network", action="store_const", const="skip-network", dest="mode")
    p.add_argument("--execute-apply", action="store_true", dest="execute_apply")
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args(); mode = args.mode or "dry-run"
    result = run(mode, args.execute_apply)
    if args.markdown: print(json.dumps(result, ensure_ascii=False, indent=2))
    else: print(json.dumps(result, ensure_ascii=False, indent=2))
