import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from build_phase169_authoring_guide_board import build

def build_dashboard():
    b = build()["phase169_authoring_guide_board"]
    return {"phase169_authoring_guide_dashboard":{"summary":{k:b[k] for k in ["fill_guide_ready","valid_examples","invalid_examples","expectations_all_match","example_coverage_status","preflight_enabled","sandbox_all_checked","console_integrated","guard","quality_gate","cannot_conclude_guard","violations","watch_core_updated","mock_used","fixture_used","pending_created","paper_order_created","real_trade_created","target_price_created"]},"next_phase_recommendation":"Phase 170: Owner authors and submits real owner_decision_input.json using this hardened guide."}}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args(); print(json.dumps(build_dashboard(), ensure_ascii=False, indent=2))
