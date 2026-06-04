import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from build_phase168_owner_decision_board import build

def build_brief():
    b = build()["phase168_owner_decision_board"]
    return {"phase168_owner_decision_brief":{"title":"Owner Decision Submission & Activation Simulation Brief","boss_summary":{"clearest_conclusion":"Activation simulation ready; no real Watch/Core update, no trade output.","simulation_only":b["simulation_only"],"no_trade_action":True},"analyst_detail":{"coverage":"13 US semiconductor/technology candidates","cannot_conclude":["simulation_is_not_real_activation","coverage_proposal_is_not_portfolio_action"]},"mock_used":False,"fixture_used":False}}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args()
    print(json.dumps(build_brief(), ensure_ascii=False, indent=2))
