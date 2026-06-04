import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from build_phase171_apply_confirmation_board import build

def build_dashboard():
    b = build()["phase171_apply_confirmation_board"]
    return {"phase171_apply_confirmation_dashboard":{"summary":{k:b[k] for k in ["input_read","apply_ready","activated","kept","deferred","state_diff_entries","rollback_prepared","audit_entries","checklist_items","apply_not_executed","guard","quality_gate","cannot_conclude_guard","violations","watch_core_updated","mock_used","fixture_used","pending_created","paper_order_created","real_trade_created","target_price_created"]},"next_phase_recommendation":"Phase 172: Owner gives final confirmation; system executes real formal research coverage state update."}}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args(); print(json.dumps(build_dashboard(), ensure_ascii=False, indent=2))
