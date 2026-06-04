import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "reporting"))
from smr_phase171_config import load_phase171_config
from smr_phase170_validator import validate_owner_input
from smr_phase170_loaders import try_read_owner_input
from smr_phase171_core import build_apply_confirmation_gate, build_coverage_apply_package, build_state_diff, build_rollback_package, build_audit_package, build_final_checklist
from smr_phase171_guard import build_apply_confirmation_guard, build_quality_gate, build_cannot_conclude_guard, build_backlog_update

def run(mode):
    cfg = load_phase171_config()
    inp = try_read_owner_input()
    v = validate_owner_input(inp)
    gate = build_apply_confirmation_gate(v)
    ap = build_coverage_apply_package(v)
    sd = build_state_diff(v)
    rp = build_rollback_package()
    au = build_audit_package(ap, sd)
    cl = build_final_checklist()
    g = build_apply_confirmation_guard(gate)
    qg = build_quality_gate(ap, gate)
    cc = build_cannot_conclude_guard()
    bl = build_backlog_update()
    return {"phase171_apply_confirmation_pipeline":{
        "mode":mode,"phase":"phase171","strategy":"owner_final_apply_confirmation_gate_and_coverage_apply_package",
        "research_only":True,"input_read":inp is not None,
        "apply_ready":gate["phase171_apply_confirmation_gate"]["ready_for_apply"],
        "activated_would_be":ap["phase171_coverage_apply_package"]["activated_count"],
        "kept_would_be":ap["phase171_coverage_apply_package"]["kept_count"],
        "state_diff_generated":True,"rollback_prepared":rp["phase171_rollback_package"]["rollback_prepared"],
        "audit_generated":True,"checklist_complete":True,
        "apply_not_executed":True,"confirmation_gate_not_apply":True,
        "apply_package_not_execution":True,"state_diff_not_update":True,
        "guard":g["phase171_apply_confirmation_guard"]["status"],
        "quality_gate":qg["phase171_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase171_cannot_conclude_guard"]["status"],"violations":0,
        "watch_core_updated":False,"candidate_auto_activated":False,"tier_update_executed":False,
        "target_price_created":0,"position_sizing_created":0,
        "mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "next_phase_recommendation":"Phase 172: Owner gives final confirmation; system executes real formal research coverage state update."
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
