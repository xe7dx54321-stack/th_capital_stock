import json, sys, os
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(BASE))

def build():
    from smr_phase159_loaders import load_pending_candidates, load_allowed_decisions, load_forbidden_terms
    from smr_phase159_file_locator import locate_owner_input_file
    from smr_phase159_json_parser import parse_owner_decision_json
    from smr_phase159_schema_validator import validate_schema
    from smr_phase159_membership_validator import validate_candidate_membership
    from smr_phase159_decision_validator import validate_allowed_decisions
    from smr_phase159_forbidden_validator import validate_no_forbidden_terms
    from smr_phase159_tier_validator import validate_requested_tier
    from smr_phase159_completeness_checker import check_completeness
    from smr_phase159_duplicate_checker import check_duplicates
    from smr_phase159_normalization import normalize_submission
    from smr_phase159_quarantine import quarantine_invalid_input
    from smr_phase159_decision_diff import build_decision_diff
    from smr_phase159_safe_manifest import build_safe_submission_manifest
    from smr_phase159_validation_report import build_validation_report
    from smr_phase159_preview_activation import build_preview_activation
    from smr_phase159_handoff_package import build_phase157_handoff_package
    from smr_phase159_audit_trail import build_submission_audit_trail

    candidates = load_pending_candidates(); allowed = load_allowed_decisions(); forbidden = load_forbidden_terms()
    file_loc = locate_owner_input_file()
    parsed = parse_owner_decision_json(file_loc["phase159_file_locator"])
    v_schema = validate_schema(parsed["phase159_json_parser"])
    v_member = validate_candidate_membership(parsed["phase159_json_parser"],candidates)
    v_decision = validate_allowed_decisions(parsed["phase159_json_parser"],allowed)
    v_forbidden = validate_no_forbidden_terms(parsed["phase159_json_parser"],forbidden)
    v_tier = validate_requested_tier(parsed["phase159_json_parser"])
    v_complete = check_completeness(parsed["phase159_json_parser"])
    v_dupes = check_duplicates(parsed["phase159_json_parser"])
    all_v = [v_schema["phase159_schema_validator"],v_member["phase159_membership_validator"],v_decision["phase159_decision_validator"],v_forbidden["phase159_forbidden_validator"],v_tier["phase159_tier_validator"],v_complete["phase159_completeness_checker"],v_dupes["phase159_duplicate_checker"]]
    quarantine = quarantine_invalid_input(all_v)
    normalized = normalize_submission(parsed["phase159_json_parser"])
    diff = build_decision_diff(normalized["phase159_normalization"],candidates)
    safe_manifest = build_safe_submission_manifest(normalized["phase159_normalization"],quarantine["phase159_quarantine"])
    report = build_validation_report(all_v, quarantine["phase159_quarantine"])
    preview = build_preview_activation(safe_manifest["phase159_safe_manifest"])
    handoff = build_phase157_handoff_package(safe_manifest["phase159_safe_manifest"],preview["phase159_preview_activation"])
    audit = build_submission_audit_trail(file_loc["phase159_file_locator"],quarantine["phase159_quarantine"],safe_manifest["phase159_safe_manifest"])

    return {"phase159_submission_board":{
        "file_locator":file_loc["phase159_file_locator"],
        "validators":{"schema":v_schema["phase159_schema_validator"],"membership":v_member["phase159_membership_validator"],"decision":v_decision["phase159_decision_validator"],"forbidden":v_forbidden["phase159_forbidden_validator"],"tier":v_tier["phase159_tier_validator"],"completeness":v_complete["phase159_completeness_checker"],"duplicate":v_dupes["phase159_duplicate_checker"]},
        "quarantine":quarantine["phase159_quarantine"],
        "decision_diff":diff["phase159_decision_diff"],
        "safe_manifest":safe_manifest["phase159_safe_manifest"],
        "validation_report":report["phase159_validation_report"],
        "preview_activation":preview["phase159_preview_activation"],
        "handoff_package":handoff["phase159_handoff_package"],
        "audit_trail":audit["phase159_audit_trail"],
        "submission_not_execution":True,"execution_blocked":True,"watch_core_updated":False,
        "mock_used":False,"fixture_used":False,
    }}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False, default=str))
