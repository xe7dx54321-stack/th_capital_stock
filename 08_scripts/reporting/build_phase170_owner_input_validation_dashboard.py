import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from build_phase170_owner_input_validation_board import build

def build_dashboard():
    b = build()["phase170_owner_input_validation_board"]
    return {"phase170_owner_input_validation_dashboard":{"summary":{k:b[k] for k in ["input_read","validator_status","valid_entries","quarantined","missing","state_preview_entries","tier_proposals","agent_tasks","state_not_updated","guard","quality_gate","cannot_conclude_guard","violations","watch_core_updated","mock_used","fixture_used","pending_created","paper_order_created","real_trade_created","target_price_created"]},"next_phase_recommendation":"Phase 171: Owner reviews state preview and confirms activation; system executes formal state update."}}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args(); print(json.dumps(build_dashboard(), ensure_ascii=False, indent=2))
