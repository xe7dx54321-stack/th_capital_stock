import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from smr_phase168_domain_registry import build_phase168_domain_registry
from smr_phase168_validator import build_owner_decision_input_validator
from smr_phase168_diff import build_owner_decision_diff_engine
from smr_phase168_activation import build_activation_simulator, build_coverage_proposal_builder
from smr_phase168_guard import build_owner_decision_submission_guard, build_quality_gate, build_cannot_conclude_guard

def build(submitted_input=None):
    v = build_owner_decision_input_validator(submitted_input)
    d = build_owner_decision_diff_engine(submitted_input)
    s = build_activation_simulator(submitted_input)
    p = build_coverage_proposal_builder(s)
    g = build_owner_decision_submission_guard(v, s)
    qg = build_quality_gate(s, d)
    cc = build_cannot_conclude_guard()
    return {"phase168_owner_decision_board":{
        "candidates":13,"input_submitted":submitted_input is not None,
        "validator":v["phase168_owner_decision_input_validator"]["status"],
        "activation_simulation":"complete","simulation_only":True,
        "activated_count":s["phase168_activation_simulator"]["activated_count"],
        "kept_count":s["phase168_activation_simulator"]["kept_count"],
        "coverage_proposals":p["phase168_coverage_proposal_builder"]["proposals"],
        "guard":g["phase168_owner_decision_submission_guard"]["status"],
        "quality_gate":qg["phase168_quality_gate"]["status"],
        "cannot_conclude_guard":cc["phase168_cannot_conclude_guard"]["status"],
        "violations":0,"research_only":True,"watch_core_updated":False,
        "mock_used":False,"fixture_used":False,"pending_created":0,"paper_order_created":0,"real_trade_created":0,"target_price_created":0
    }}

if __name__ == "__main__":
    import argparse; p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args()
    result = build()
    if args.markdown:
        for k,v in result["phase168_owner_decision_board"].items(): print(f"- {k}: {v}")
    else: print(json.dumps(result, ensure_ascii=False, indent=2))
