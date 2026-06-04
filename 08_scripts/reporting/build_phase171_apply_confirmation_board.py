import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase170_validator import validate_owner_input
from smr_phase170_loaders import try_read_owner_input
from smr_phase171_core import build_apply_confirmation_gate, build_coverage_apply_package, build_state_diff, build_rollback_package, build_audit_package, build_final_checklist
from smr_phase171_guard import build_apply_confirmation_guard, build_quality_gate, build_cannot_conclude_guard

def build():
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
    return {"phase171_apply_confirmation_board":{
        "input_read":inp is not None,"apply_ready":gate["phase171_apply_confirmation_gate"]["ready_for_apply"],
        "activated":ap["phase171_coverage_apply_package"]["activated_count"],
        "kept":ap["phase171_coverage_apply_package"]["kept_count"],
        "deferred":ap["phase171_coverage_apply_package"]["deferred_count"],
        "state_diff_entries":sd["phase171_state_diff"]["entries"],
        "rollback_prepared":rp["phase171_rollback_package"]["rollback_prepared"],
        "audit_entries":au["phase171_audit_package"]["audit_entries"],
        "checklist_items":cl["phase171_final_checklist"]["item_count"],
        "apply_not_executed":True,
        "guard":g["phase171_apply_confirmation_guard"]["status"],
        "quality_gate":qg["phase171_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase171_cannot_conclude_guard"]["status"],"violations":0,
        "research_only":True,"watch_core_updated":False,
        "mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_created":0
    }}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args(); result = build()
    if args.markdown:
        for k,v in result["phase171_apply_confirmation_board"].items(): print(f"- {k}: {v}")
    else: print(json.dumps(result, ensure_ascii=False, indent=2))
