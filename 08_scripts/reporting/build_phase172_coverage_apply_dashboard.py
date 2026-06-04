import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from build_phase172_coverage_apply_board import build

def build_dashboard():
    b = build()["phase172_coverage_apply_board"]
    return {"phase172_coverage_apply_dashboard":{"summary":{k:b[k] for k in ["input_read","prerequisites_met","execute_apply_flag","can_execute","applied","candidates_updated","coverage_state_only","trade_state_unchanged","state_path_ignored","guard","quality_gate","cannot_conclude_guard","violations","watch_core_updated","mock_used","fixture_used","pending_created","paper_order_created","real_trade_created","target_price_created"]},"next_phase_recommendation":"Phase 173: With formal coverage state applied, integrate activated candidates into daily monitoring and research pipeline."}}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args(); print(json.dumps(build_dashboard(), ensure_ascii=False, indent=2))
