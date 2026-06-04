import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from build_phase173_owner_preparation_board import build

def build_dashboard():
    b = build()["phase173_owner_preparation_board"]
    return {"phase173_owner_preparation_dashboard":{"summary":{k:b[k] for k in ["recommendations","activated_suggested","kept_suggested","deferred_suggested","rejected_suggested","json_draft_ready","draft_not_real_input","checklist_items","confirmation_pack_ready","instructions_ready","guard","quality_gate","cannot_conclude_guard","violations","watch_core_updated","mock_used","fixture_used","pending_created","paper_order_created","real_trade_created","target_price_created"]},"next_phase_recommendation":"OWNER_ACTION: Copy draft to owner_decision_input.json, review, sign final confirmation, then execute: python run_phase172_coverage_apply_pipeline.py --execute --execute-apply --json"}}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args(); print(json.dumps(build_dashboard(), ensure_ascii=False, indent=2))
