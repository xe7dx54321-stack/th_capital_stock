import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build():
    from smr_phase154_loaders import load_phase153_onboarding_packets, load_phase150_tier_assignments
    from smr_phase154_loop_input_selector import build_loop_input_selector
    from smr_phase154_opportunity_agent import run_opportunity_agent
    from smr_phase154_evidence_agent import run_evidence_agent
    from smr_phase154_risk_agent import run_risk_agent
    from smr_phase154_thesis_agent import run_thesis_agent
    from smr_phase154_deep_dive_agent import run_deep_dive_agent
    from smr_phase154_brief_agent import run_brief_agent
    from smr_phase154_feedback_agent import run_feedback_agent
    from smr_phase154_judge_agent_loop import run_judge_agent_loop
    from smr_phase154_handoff_chain import build_handoff_chain
    from smr_phase154_memory_update import build_loop_memory_update
    from smr_phase154_task_queue_update import build_task_queue_update
    from smr_phase154_thesis_proposal import build_thesis_proposal
    from smr_phase154_evidence_delta import build_evidence_delta
    from smr_phase154_risk_delta import build_risk_delta
    from smr_phase154_owner_action_proposal import build_owner_action_proposal

    tier_assignments = load_phase150_tier_assignments()
    onboarding = load_phase153_onboarding_packets()
    input_sel = build_loop_input_selector(tier_assignments, onboarding)
    targets = input_sel["phase154_loop_input_selector"]["all_targets"]

    opp = run_opportunity_agent(targets)
    ev = run_evidence_agent(targets, opp)
    risk = run_risk_agent(targets, ev)
    thesis = run_thesis_agent(targets, risk)
    dd = run_deep_dive_agent(targets, thesis)
    brief = run_brief_agent(targets, dd)
    fb = run_feedback_agent(targets, brief)
    judge = run_judge_agent_loop(targets, [opp, ev, risk, thesis, dd, brief, fb])

    handoff = build_handoff_chain()
    memory = build_loop_memory_update(targets, [opp, ev, risk, thesis, dd, brief, fb, judge])
    queue = build_task_queue_update(targets)
    thesis_prop = build_thesis_proposal(targets)
    ev_delta = build_evidence_delta(targets)
    risk_delta = build_risk_delta(targets)
    owner = build_owner_action_proposal(targets)

    return {"phase154_loop_research_board": {
        "loop_targets_total": len(targets),
        "loop_input": input_sel["phase154_loop_input_selector"],
        "agents": {"opportunity": opp["phase154_opportunity_agent"], "evidence": ev["phase154_evidence_agent"],
                   "risk": risk["phase154_risk_agent"], "thesis": thesis["phase154_thesis_agent"],
                   "deep_dive": dd["phase154_deep_dive_agent"], "brief": brief["phase154_brief_agent"],
                   "feedback": fb["phase154_feedback_agent"], "judge": judge["phase154_judge_agent_loop"]},
        "handoff_chain": handoff["phase154_handoff_chain"],
        "memory_update": memory["phase154_memory_update"],
        "task_queue": queue["phase154_task_queue_update"],
        "thesis_proposals": thesis_prop["phase154_thesis_proposal"],
        "evidence_delta": ev_delta["phase154_evidence_delta"],
        "risk_delta": risk_delta["phase154_risk_delta"],
        "owner_actions": owner["phase154_owner_action_proposal"],
        "agent_simulation_only": True, "live_llm_call_made": False,
        "research_only": True, "watch_core_updated": False, "candidate_auto_activated": False,
        "mock_used": False, "fixture_used": False,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
