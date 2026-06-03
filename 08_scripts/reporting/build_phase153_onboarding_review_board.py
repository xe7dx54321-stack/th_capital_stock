import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build():
    from smr_phase153_loaders import load_phase152_admitted_candidates
    from smr_phase153_identity_review import build_identity_review_packet
    from smr_phase153_source_route_review import build_source_route_review_packet
    from smr_phase153_financial_route_review import build_financial_route_review_packet
    from smr_phase153_valuation_route_review import build_valuation_route_review_packet
    from smr_phase153_evidence_review import build_evidence_review_packet
    from smr_phase153_risk_review import build_risk_review_packet
    from smr_phase153_thesis_seed_review import build_thesis_seed_review_packet
    from smr_phase153_owner_checklist import build_owner_approval_checklist
    from smr_phase153_judge_review import build_judge_agent_review_packet
    from smr_phase153_judge_classifier import classify_judge_decisions
    from smr_phase153_agent_followup import build_agent_followup_routes
    from smr_phase153_readiness_classifier import classify_onboarding_readiness
    from smr_phase153_activation_eligibility import classify_activation_eligibility
    from smr_phase153_approval_queue import build_manual_approval_queue

    candidates = load_phase152_admitted_candidates()
    packets_data = []
    for c in candidates:
        review_packets = {
            "identity_review": build_identity_review_packet(c),
            "source_route_review": build_source_route_review_packet(c),
            "financial_route_review": build_financial_route_review_packet(c),
            "valuation_route_review": build_valuation_route_review_packet(c),
            "evidence_requirement_review": build_evidence_review_packet(c),
            "risk_limitation_review": build_risk_review_packet(c),
            "initial_thesis_seed_review": build_thesis_seed_review_packet(c),
            "owner_approval_checklist": build_owner_approval_checklist(c),
        }
        review_packets["judge_agent_review"] = build_judge_agent_review_packet(c, review_packets)
        packets_data.append({"ticker": c["ticker"], "name": c.get("name", ""), "market": c.get("market", ""),
                            "review_packets": review_packets,
                            "judge_decision": review_packets["judge_agent_review"]["judge_decision"]})

    judge_result = classify_judge_decisions(packets_data)
    followup = build_agent_followup_routes(judge_result["phase153_judge_classifier"])
    readiness = classify_onboarding_readiness(packets_data)
    eligibility = classify_activation_eligibility(readiness["phase153_readiness_classifier"])
    approval_queue = build_manual_approval_queue(eligibility["phase153_activation_eligibility"])

    return {"phase153_onboarding_review_board": {
        "candidates_reviewed": len(packets_data),
        "packets": packets_data,
        "judge_summary": judge_result["phase153_judge_classifier"]["summary"],
        "agent_followup": followup["phase153_agent_followup"],
        "readiness": readiness["phase153_readiness_classifier"]["summary"],
        "eligibility": eligibility["phase153_activation_eligibility"]["results"],
        "approval_queue": approval_queue["phase153_approval_queue"],
        "onboarding_review_is_research_only": True,
        "judge_pass_not_investment_approval": True,
        "activation_disabled": True,
        "mock_used": False, "fixture_used": False,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
