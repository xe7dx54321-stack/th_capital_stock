import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from build_phase168_owner_decision_board import build

def build_dashboard():
    b = build()["phase168_owner_decision_board"]
    return {"phase168_owner_decision_dashboard":{"summary":{"candidates":b["candidates"],"input_submitted":b["input_submitted"],"simulation_only":b["simulation_only"],"activated_count":b["activated_count"],"kept_count":b["kept_count"],"coverage_proposals":b["coverage_proposals"],"guard":b["guard"],"quality_gate":b["quality_gate"],"violations":b["violations"],"watch_core_updated":b["watch_core_updated"],"mock_used":b["mock_used"],"fixture_used":b["fixture_used"],"pending_created":b["pending_created"],"paper_order_created":b["paper_order_created"],"real_trade_created":b["real_trade_created"],"target_price_created":b["target_price_created"],"next_phase_recommendation":"Phase 169: Formal research coverage integration for activated candidates."}}}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args()
    print(json.dumps(build_dashboard(), ensure_ascii=False, indent=2))
