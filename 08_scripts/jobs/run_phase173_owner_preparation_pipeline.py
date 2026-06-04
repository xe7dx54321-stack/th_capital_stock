import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "reporting"))
from smr_phase173_core import build_candidate_recommendation_draft, build_fill_ready_json_draft, build_preflight_checklist, build_final_confirmation_pack, build_execute_apply_instructions
from smr_phase173_guard import build_owner_preparation_guard, build_quality_gate, build_cannot_conclude_guard, build_backlog_update

def run(mode):
    rec = build_candidate_recommendation_draft()
    js = build_fill_ready_json_draft()
    cl = build_preflight_checklist()
    cf = build_final_confirmation_pack()
    ins = build_execute_apply_instructions()
    g = build_owner_preparation_guard()
    qg = build_quality_gate(rec, js)
    cc = build_cannot_conclude_guard()
    bl = build_backlog_update()
    return {"phase173_owner_preparation_pipeline":{
        "mode":mode,"phase":"phase173","strategy":"owner_decision_input_preparation_and_final_confirmation_pack",
        "research_only":True,
        "recommendations":rec["phase173_candidate_recommendation_draft"]["entries"],
        "activated_suggested":rec["phase173_candidate_recommendation_draft"]["activated"],
        "kept_suggested":rec["phase173_candidate_recommendation_draft"]["kept"],
        "deferred_suggested":rec["phase173_candidate_recommendation_draft"]["deferred"],
        "rejected_suggested":rec["phase173_candidate_recommendation_draft"]["rejected"],
        "json_draft_ready":js["phase173_fill_ready_json_draft"]["draft_generated"],
        "draft_not_real_input":js["phase173_fill_ready_json_draft"]["draft_not_real_input"],
        "auto_write_disabled":js["phase173_fill_ready_json_draft"]["auto_write_disabled"],
        "checklist_items":cl["phase173_preflight_checklist"]["item_count"],
        "confirmation_pack_ready":True,"instructions_ready":True,
        "guard":g["phase173_owner_preparation_guard"]["status"],
        "quality_gate":qg["phase173_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase173_cannot_conclude_guard"]["status"],"violations":0,
        "recommendation_not_owner_decision":True,"draft_not_auto_filled":True,
        "instructions_not_auto_execute":True,
        "watch_core_updated":False,"candidate_auto_activated":False,"tier_update_executed":False,
        "target_price_created":0,"position_sizing_created":0,
        "mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,
        "next_phase_recommendation":"OWNER_ACTION: Copy draft to owner_decision_input.json, review, sign final confirmation, then execute: python run_phase172_coverage_apply_pipeline.py --execute --execute-apply --json"
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
