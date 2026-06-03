import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build():
    from smr_phase157_loaders import load_ready_candidates
    from smr_phase157_template_exporter import export_decision_template
    from smr_phase157_template_importer import import_decision_template
    from smr_phase157_decision_parser import parse_owner_decisions
    from smr_phase157_decision_validator import validate_owner_decisions
    from smr_phase157_invalid_rejector import reject_invalid_decisions
    from smr_phase157_decision_summary import classify_owner_decision_summary
    from smr_phase157_approved_simulator import simulate_approved_activation
    from smr_phase157_defer_simulator import simulate_defer
    from smr_phase157_evidence_simulator import simulate_more_evidence
    from smr_phase157_identity_source_simulator import simulate_identity_source_confirmation
    from smr_phase157_reject_simulator import simulate_reject_for_now
    from smr_phase157_execution_simulator import simulate_execution_plan
    from smr_phase157_agent_task_simulator import simulate_agent_task_queue
    from smr_phase157_tier_proposal_diff import build_tier_proposal_diff
    from smr_phase157_dependency_checker import check_activation_dependencies
    from smr_phase157_rollback_plan import build_rollback_plan
    from smr_phase157_audit_trail import build_decision_audit_trail

    candidates = load_ready_candidates()
    exported = export_decision_template(candidates)
    imported = import_decision_template(None, candidates)
    parsed = parse_owner_decisions(imported["phase157_template_importer"])
    validator = validate_owner_decisions(parsed["phase157_decision_parser"])
    rejector = reject_invalid_decisions(validator["phase157_decision_validator"])
    summary = classify_owner_decision_summary(parsed["phase157_decision_parser"],imported["phase157_template_importer"])

    approved_sim = simulate_approved_activation([])
    defer_sim = simulate_defer([])
    ev_sim = simulate_more_evidence([])
    id_sim = simulate_identity_source_confirmation([])
    rej_sim = simulate_reject_for_now([])
    exec_plan = simulate_execution_plan(approved_sim["phase157_approved_simulator"])
    agent_task = simulate_agent_task_queue(exec_plan["phase157_execution_simulator"])
    tier_diff = build_tier_proposal_diff(summary["phase157_decision_summary"]["summary"])
    deps = check_activation_dependencies(exec_plan["phase157_execution_simulator"])
    rollback = build_rollback_plan()
    audit = build_decision_audit_trail(summary["phase157_decision_summary"])

    return {"phase157_decision_board":{
        "template_export":exported["phase157_template_exporter"],
        "template_import":imported["phase157_template_importer"],
        "decision_summary":summary["phase157_decision_summary"],
        "simulations":{"approved":approved_sim["phase157_approved_simulator"],"defer":defer_sim["phase157_defer_simulator"],"more_evidence":ev_sim["phase157_evidence_simulator"],"identity_source":id_sim["phase157_identity_source_simulator"],"reject":rej_sim["phase157_reject_simulator"]},
        "execution_plan":exec_plan["phase157_execution_simulator"],
        "agent_tasks":agent_task["phase157_agent_task_simulator"],
        "tier_proposal_diff":tier_diff["phase157_tier_proposal_diff"],
        "dependencies":deps["phase157_dependency_checker"],
        "rollback":rollback["phase157_rollback_plan"],
        "audit":audit["phase157_audit_trail"],
        "simulation_only":True,"execution_blocked":True,"owner_input_present":False,
        "watch_core_updated":False,"candidate_auto_activated":False,
        "mock_used":False,"fixture_used":False,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
