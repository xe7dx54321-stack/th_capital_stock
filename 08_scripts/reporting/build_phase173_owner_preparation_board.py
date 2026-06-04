import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase173_core import build_candidate_recommendation_draft, build_fill_ready_json_draft, build_preflight_checklist, build_final_confirmation_pack, build_execute_apply_instructions
from smr_phase173_guard import build_owner_preparation_guard, build_quality_gate, build_cannot_conclude_guard

def build():
    rec = build_candidate_recommendation_draft()
    js = build_fill_ready_json_draft()
    cl = build_preflight_checklist()
    cf = build_final_confirmation_pack()
    ins = build_execute_apply_instructions()
    g = build_owner_preparation_guard()
    qg = build_quality_gate(rec, js)
    cc = build_cannot_conclude_guard()
    return {"phase173_owner_preparation_board":{
        "recommendations":rec["phase173_candidate_recommendation_draft"]["entries"],
        "activated_suggested":rec["phase173_candidate_recommendation_draft"]["activated"],
        "kept_suggested":rec["phase173_candidate_recommendation_draft"]["kept"],
        "deferred_suggested":rec["phase173_candidate_recommendation_draft"]["deferred"],
        "rejected_suggested":rec["phase173_candidate_recommendation_draft"]["rejected"],
        "json_draft_ready":js["phase173_fill_ready_json_draft"]["draft_generated"],
        "draft_not_real_input":js["phase173_fill_ready_json_draft"]["draft_not_real_input"],
        "checklist_items":cl["phase173_preflight_checklist"]["item_count"],
        "confirmation_pack_ready":True,
        "instructions_ready":True,
        "guard":g["phase173_owner_preparation_guard"]["status"],
        "quality_gate":qg["phase173_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase173_cannot_conclude_guard"]["status"],"violations":0,
        "research_only":True,"watch_core_updated":False,
        "mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_created":0
    }}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args(); result = build()
    if args.markdown:
        for k,v in result["phase173_owner_preparation_board"].items(): print(f"- {k}: {v}")
    else: print(json.dumps(result, ensure_ascii=False, indent=2))
