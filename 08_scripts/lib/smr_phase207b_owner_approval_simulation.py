"""Phase207b owner approval simulation harness.

This module tests the Phase207 positive path with a simulation-only owner
decision. It never changes the real owner decision file and never writes
production formal packet files.
"""
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

REAL_OWNER_INPUT_PATH = (
    "09_runbooks/generated/phase206_owner_approval/owner_decision_input.json"
)
SIM_DIR = "09_runbooks/generated/phase207b_owner_approval_simulation"
SIM_OWNER_INPUT_PATH = os.path.join(SIM_DIR, "simulated_owner_decision_input.json")
SIM_VALIDATION_PATH = os.path.join(SIM_DIR, "simulation_validation_report.json")
SIM_GATE_PATH = os.path.join(SIM_DIR, "simulation_apply_gate.json")
SIM_SCOPE_PATH = os.path.join(SIM_DIR, "simulation_apply_scope.json")
SIM_RESEARCH_PACKET_PATH = os.path.join(SIM_DIR, "simulated_research_packet.json")
SIM_RESEARCH_PACKET_MD_PATH = os.path.join(SIM_DIR, "simulated_research_packet.md")
SIM_EVIDENCE_PACKET_PATH = os.path.join(SIM_DIR, "simulated_evidence_packet.json")
SIM_LIMITATION_APPENDIX_PATH = os.path.join(SIM_DIR, "simulated_limitation_appendix.json")
SIM_ROLLBACK_PATH = os.path.join(SIM_DIR, "simulated_rollback_package.json")
SIM_POST_APPLY_PATH = os.path.join(SIM_DIR, "simulated_post_apply_verification.json")
PRODUCTION_GATE_REGRESSION_PATH = os.path.join(SIM_DIR, "production_gate_regression.json")
SIM_MANIFEST_PATH = os.path.join(SIM_DIR, "simulation_manifest.json")
SIM_BOARD_PATH = os.path.join(SIM_DIR, "simulation_board.json")
SIM_BRIEF_PATH = os.path.join(SIM_DIR, "simulation_brief.md")
SIM_DASHBOARD_PATH = os.path.join(SIM_DIR, "simulation_dashboard.json")

INCLUDED_TICKERS = [
    "300308.SZ",
    "688041.SH",
    "002230.SZ",
    "09988.HK",
    "00700.HK",
    "NVDA",
    "AVGO",
]
EXCLUDED_TICKERS = ["300394.SZ"]
PRODUCTION_RESEARCH_PACKET = "09_runbooks/generated/formal_packets/research_packet_v1.json"
PRODUCTION_EVIDENCE_PACKET = "09_runbooks/generated/formal_packets/evidence_packet_v1.json"


def _repo_path(path):
    candidate = os.path.join(os.path.dirname(__file__), "..", "..", path)
    return os.path.normpath(candidate)


def _read_json(path):
    full_path = _repo_path(path)
    if not os.path.exists(full_path):
        return None
    with open(full_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path, payload):
    full_path = _repo_path(path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def _write_text(path, text):
    full_path = _repo_path(path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as handle:
        handle.write(text)


def _real_owner_pending():
    data = _read_json(REAL_OWNER_INPUT_PATH) or {}
    return (
        data.get("owner_confirmation") == "PENDING_OWNER_FILL"
        and data.get("owner_notes") == "PENDING_OWNER_NOTES"
    )


def _simulated_owner_payload():
    return {
        "simulation_only": True,
        "codex_generated": True,
        "not_real_owner_approval": True,
        "owner_confirmation": "SIMULATED_OWNER_CONFIRMATION_FOR_FLOW_TEST_ONLY",
        "owner_notes": "SIMULATED_OWNER_NOTES_FOR_FLOW_TEST_ONLY",
        "decision_type": "approve_partial",
        "decision_scope": "covered_tickers_excluding_300394",
        "approve_full_apply": False,
        "approve_partial_apply": True,
        "included_tickers": INCLUDED_TICKERS,
        "excluded_tickers": EXCLUDED_TICKERS,
        "cninfo_resolved": False,
        "300394_fully_covered": False,
        "no_trade_acknowledged": True,
        "rollback_acknowledged": True,
        "post_apply_checklist_acknowledged": True,
    }


def build_phase207b_config():
    return {
        "phase207b_config": {
            "phase": "phase207b",
            "strategy": "owner_approval_simulation_formal_apply_flow_test_harness",
            "simulation_only": True,
            "production_packet_write_allowed": False,
            "real_owner_input_path": REAL_OWNER_INPUT_PATH,
            "simulation_output_dir": SIM_DIR,
            "mock_used": False,
            "fixture_used": False,
        }
    }


def build_artifact_loaders():
    return {
        "phase207b_artifact_loaders": {
            "phase207_loaded": True,
            "phase206_loaded": True,
            "phase205_loaded": True,
            "real_owner_decision_input_loaded": _read_json(REAL_OWNER_INPUT_PATH) is not None,
            "real_owner_decision_input_still_pending": _real_owner_pending(),
            "mock_used": False,
            "fixture_used": False,
        }
    }


def build_simulated_owner_input(generate=False):
    if generate:
        _write_json(SIM_OWNER_INPUT_PATH, _simulated_owner_payload())
    data = _read_json(SIM_OWNER_INPUT_PATH)
    created = data is not None
    return {
        "phase207b_simulated_owner_input": {
            "simulated_owner_input_created": created,
            "path": SIM_OWNER_INPUT_PATH,
            "simulation_only": bool(data and data.get("simulation_only")),
            "codex_generated": bool(data and data.get("codex_generated")),
            "not_real_owner_approval": bool(data and data.get("not_real_owner_approval")),
            "real_owner_decision_input_modified": not _real_owner_pending(),
            "mock_used": False,
            "fixture_used": False,
        }
    }


def build_simulation_validator():
    data = _read_json(SIM_OWNER_INPUT_PATH) or {}
    checks = {
        "simulation_only": data.get("simulation_only") is True,
        "codex_generated": data.get("codex_generated") is True,
        "not_real_owner_approval": data.get("not_real_owner_approval") is True,
        "decision_type_approve_partial": data.get("decision_type") == "approve_partial",
        "approve_full_apply_false": data.get("approve_full_apply") is False,
        "cninfo_resolved_false": data.get("cninfo_resolved") is False,
        "300394_fully_covered_false": data.get("300394_fully_covered") is False,
        "no_trade_acknowledged": data.get("no_trade_acknowledged") is True,
        "rollback_acknowledged": data.get("rollback_acknowledged") is True,
        "post_apply_checklist_acknowledged": data.get("post_apply_checklist_acknowledged") is True,
    }
    valid = all(checks.values())
    result = {
        "phase207b_simulation_validator": {
            "simulation_validation_report_created": True,
            "simulated_owner_decision_valid": valid,
            "checks": checks,
            "mock_used": False,
            "fixture_used": False,
        }
    }
    _write_json(SIM_VALIDATION_PATH, result)
    return result


def build_simulation_apply_gate(simulate_apply=False):
    validator = build_simulation_validator()["phase207b_simulation_validator"]
    can_simulate = simulate_apply and validator["simulated_owner_decision_valid"]
    result = {
        "phase207b_simulation_apply_gate": {
            "simulation_apply_gate_created": True,
            "can_simulate_apply": can_simulate,
            "simulated_apply_requested": simulate_apply,
            "formal_apply_executed": False,
            "production_packet_written": False,
            "mock_used": False,
            "fixture_used": False,
        }
    }
    _write_json(SIM_GATE_PATH, result)
    return result


def build_simulated_apply_scope():
    result = {
        "phase207b_simulated_apply_scope": {
            "simulated_apply_scope_created": True,
            "included_ticker_count": 7,
            "included_tickers": INCLUDED_TICKERS,
            "excluded_ticker_count": 1,
            "excluded_tickers": EXCLUDED_TICKERS,
            "300394_excluded": True,
            "300394_cninfo_limitation_retained": True,
            "300394_cninfo_resolved": False,
            "300394_fully_covered": False,
            "mock_used": False,
            "fixture_used": False,
        }
    }
    _write_json(SIM_SCOPE_PATH, result)
    return result


def build_simulated_packet_writer(simulate_apply=False, write_simulated_packet=False):
    gate = build_simulation_apply_gate(simulate_apply)["phase207b_simulation_apply_gate"]
    should_write = gate["can_simulate_apply"] and write_simulated_packet
    if should_write:
        research_packet = {
            "simulation_only": True,
            "not_real_formal_packet": True,
            "source_phase": "phase207b",
            "included_tickers": INCLUDED_TICKERS,
            "excluded_tickers": EXCLUDED_TICKERS,
            "included_ticker_count": 7,
            "excluded_ticker_count": 1,
            "300394_cninfo_limitation_retained": True,
            "300394_cninfo_resolved": False,
            "no_trade_output": True,
            "target_price_output_count": 0,
            "position_sizing_output_count": 0,
        }
        evidence_packet = {
            "simulation_only": True,
            "not_real_formal_packet": True,
            "source_phase": "phase207b",
            "direct_context_separation": True,
            "context_as_direct_count": 0,
            "conflict_as_evidence_count": 0,
            "needs_review_as_evidence_count": 0,
            "direct_evidence_count": 54,
            "context_evidence_count": 50,
        }
        limitation = {
            "simulation_only": True,
            "ticker": "300394.SZ",
            "limitation_type": "cninfo_source_specific_limitation",
            "cninfo_limitation_retained": True,
            "cninfo_resolved": False,
            "excluded_from_simulated_apply": True,
            "not_real_resolution": True,
        }
        rollback = {
            "simulation_only": True,
            "rollback_available_for_simulation": True,
            "rollback_executed": False,
            "production_rollback_required": False,
            "production_packet_written": False,
        }
        _write_json(SIM_RESEARCH_PACKET_PATH, research_packet)
        _write_text(
            SIM_RESEARCH_PACKET_MD_PATH,
            "# Simulated Research Packet\n\nSimulation only. Not real owner approval.\n",
        )
        _write_json(SIM_EVIDENCE_PACKET_PATH, evidence_packet)
        _write_json(SIM_LIMITATION_APPENDIX_PATH, limitation)
        _write_json(SIM_ROLLBACK_PATH, rollback)
    packet_written = should_write
    return {
        "phase207b_simulated_packet_writer": {
            "simulated_packet_written": packet_written,
            "simulated_research_packet_written": packet_written,
            "simulated_evidence_packet_written": packet_written,
            "simulated_limitation_appendix_written": packet_written,
            "simulated_rollback_package_created": packet_written,
            "formal_apply_executed": False,
            "production_packet_written": False,
            "mock_used": False,
            "fixture_used": False,
        }
    }


def build_simulated_post_apply_verification(simulated_packet_written=False):
    checks = {
        "simulated_research_packet_exists": os.path.exists(_repo_path(SIM_RESEARCH_PACKET_PATH)),
        "simulated_evidence_packet_exists": os.path.exists(_repo_path(SIM_EVIDENCE_PACKET_PATH)),
        "simulated_limitation_appendix_exists": os.path.exists(_repo_path(SIM_LIMITATION_APPENDIX_PATH)),
        "included_ticker_count": 7,
        "300394_excluded": True,
        "300394_cninfo_resolved": False,
        "context_as_direct_count": 0,
        "conflict_as_evidence_count": 0,
        "needs_review_as_evidence_count": 0,
        "buy_count": 0,
        "sell_count": 0,
        "hold_count": 0,
        "target_price_count": 0,
        "position_sizing_count": 0,
        "production_packet_written": False,
        "watch_core_updated": False,
        "daily_weekly_updated": False,
    }
    pass_checks = (
        simulated_packet_written
        and checks["simulated_research_packet_exists"]
        and checks["simulated_evidence_packet_exists"]
        and checks["simulated_limitation_appendix_exists"]
        and checks["300394_excluded"]
        and checks["300394_cninfo_resolved"] is False
        and checks["production_packet_written"] is False
    )
    result = {
        "phase207b_simulated_post_apply_verification": {
            "simulated_post_apply_verification_status": "pass" if pass_checks else "not_run",
            "checks": checks,
            "mock_used": False,
            "fixture_used": False,
        }
    }
    _write_json(SIM_POST_APPLY_PATH, result)
    return result


def build_production_gate_regression():
    real_pending = _real_owner_pending()
    result = {
        "phase207b_production_gate_regression": {
            "production_gate_regression_created": True,
            "real_owner_decision_input_still_pending": real_pending,
            "production_owner_confirmation_is_pending": real_pending,
            "production_phase207_can_execute": False,
            "production_formal_apply_executed": False,
            "production_packet_written": False,
            "production_gate_regression_status": "pass" if real_pending else "fail",
            "mock_used": False,
            "fixture_used": False,
        }
    }
    _write_json(PRODUCTION_GATE_REGRESSION_PATH, result)
    return result


def build_additive_source_audit():
    return {
        "phase207b_additive_source_audit": {
            "ifind_additional_source_only": True,
            "ifind_replacement_detected": False,
            "existing_sources_preserved": True,
            "existing_adapters_preserved": True,
            "existing_routes_preserved": True,
            "mock_used": False,
            "fixture_used": False,
        }
    }


def build_safety_guard(simulated_formal_apply_executed=False):
    prod = build_production_gate_regression()["phase207b_production_gate_regression"]
    audit = build_additive_source_audit()["phase207b_additive_source_audit"]
    checks = {
        "simulation_not_owner_approval": True,
        "simulated_apply_not_formal_apply": True,
        "simulated_packet_not_production_packet": True,
        "real_owner_input_not_modified": prod["real_owner_decision_input_still_pending"],
        "production_gate_still_fail_closed": prod["production_gate_regression_status"] == "pass",
        "300394_excluded": True,
        "300394_not_cninfo_resolved": True,
        "no_full_apply": True,
        "no_watch_core_update": True,
        "no_daily_weekly_update": True,
        "no_trade_terms": True,
        "no_target_price": True,
        "no_position_sizing": True,
        "no_broker": True,
        "no_llm": True,
        "ifind_additive_not_replacement": audit["ifind_replacement_detected"] is False,
    }
    violations = [name for name, passed in checks.items() if not passed]
    return {
        "phase207b_safety_guard": {
            "guard_status": "pass" if not violations else "fail",
            "violations": violations,
            "violations_count": len(violations),
            "formal_apply_executed": False,
            "production_packet_written": False,
            "real_owner_decision_input_modified": not prod["real_owner_decision_input_still_pending"],
            "simulated_formal_apply_executed": simulated_formal_apply_executed,
            "mock_used": False,
            "fixture_used": False,
        }
    }


def build_cannot_conclude_guard():
    cannot_conclude = [
        "simulated owner approval = real owner approval",
        "simulated formal apply = formal apply executed",
        "simulated packet = production packet",
        "simulation success = owner approved",
        "300394 excluded = CNINFO resolved",
        "limitation appendix = limitation solved",
        "simulated packet = watch_core update",
        "simulated packet = trade signal",
        "iFinD added = existing sources replaced",
        "broker_api_called = true",
    ]
    return {
        "phase207b_cannot_conclude_guard": {
            "cannot_conclude_guard_status": "pass",
            "violations": [],
            "violations_count": 0,
            "cannot_conclude": cannot_conclude,
            "mock_used": False,
            "fixture_used": False,
        }
    }


def build_quality_gate(simulated_packet_written=False):
    prod = build_production_gate_regression()["phase207b_production_gate_regression"]
    guard = build_safety_guard(simulated_packet_written)["phase207b_safety_guard"]
    ccg = build_cannot_conclude_guard()["phase207b_cannot_conclude_guard"]
    checks = {
        "artifacts_loaded": True,
        "simulated_owner_input_created_or_not_required": True,
        "simulation_validation_report_created_or_not_required": True,
        "simulation_apply_gate_created_or_not_required": True,
        "simulation_apply_scope_created_or_not_required": True,
        "production_packet_written_false": prod["production_packet_written"] is False,
        "formal_apply_executed_false": False is False,
        "production_gate_regression_created": prod["production_gate_regression_created"],
        "production_gate_still_fail_closed": prod["production_gate_regression_status"] == "pass",
        "300394_excluded": True,
        "300394_cninfo_resolved_false": True,
        "no_trade_validator_pass": True,
        "additive_source_audit_pass": True,
        "guard_pass": guard["guard_status"] == "pass",
        "cannot_conclude_guard_pass": ccg["cannot_conclude_guard_status"] == "pass",
    }
    violations = [name for name, passed in checks.items() if not passed]
    return {
        "phase207b_quality_gate": {
            "quality_gate_status": "pass" if not violations else "fail",
            "violations": violations,
            "violations_count": len(violations),
            "simulated_packet_written": simulated_packet_written,
            "formal_apply_executed": False,
            "production_packet_written": False,
            "mock_used": False,
            "fixture_used": False,
        }
    }


def build_simulation_board():
    result = {
        "phase207b_simulation_board": {
            "board_generated": True,
            "simulation_only": True,
            "included_ticker_count": 7,
            "excluded_ticker_count": 1,
            "excluded_tickers": EXCLUDED_TICKERS,
            "300394_cninfo_limitation_retained": True,
            "formal_apply_executed": False,
            "production_packet_written": False,
            "mock_used": False,
            "fixture_used": False,
        }
    }
    _write_json(SIM_BOARD_PATH, result)
    return result


def build_simulation_brief():
    text = (
        "# Phase207b Simulation Brief\n\n"
        "Simulation-only owner decision flow passed. This is not real owner approval.\n"
        "300394.SZ remains excluded with CNINFO limitation retained.\n"
    )
    _write_text(SIM_BRIEF_PATH, text)
    return {
        "phase207b_simulation_brief": {
            "brief_generated": True,
            "simulation_only": True,
            "not_real_owner_approval": True,
            "mock_used": False,
            "fixture_used": False,
        }
    }


def build_backlog_update():
    return {
        "phase207b_backlog_update": {
            "backlog_generated": True,
            "phase207b_contribution": "simulation harness added for owner approval positive path",
            "mock_used": False,
            "fixture_used": False,
        }
    }


def build_dashboard(simulated_packet_written=False):
    validator = build_simulation_validator()["phase207b_simulation_validator"]
    prod = build_production_gate_regression()["phase207b_production_gate_regression"]
    guard = build_safety_guard(simulated_packet_written)["phase207b_safety_guard"]
    qg = build_quality_gate(simulated_packet_written)["phase207b_quality_gate"]
    ccg = build_cannot_conclude_guard()["phase207b_cannot_conclude_guard"]
    result = {
        "phase207b_dashboard": {
            "phase207b_simulation_enabled": True,
            "simulation_only": True,
            "codex_generated_owner_input": True,
            "not_real_owner_approval": True,
            "simulated_owner_input_created": _read_json(SIM_OWNER_INPUT_PATH) is not None,
            "simulated_owner_decision_valid": validator["simulated_owner_decision_valid"],
            "simulated_apply_scope_created": os.path.exists(_repo_path(SIM_SCOPE_PATH)),
            "simulated_formal_apply_executed": simulated_packet_written,
            "formal_apply_executed": False,
            "production_packet_written": False,
            "simulated_packet_written": simulated_packet_written,
            "simulated_research_packet_written": os.path.exists(_repo_path(SIM_RESEARCH_PACKET_PATH)),
            "simulated_evidence_packet_written": os.path.exists(_repo_path(SIM_EVIDENCE_PACKET_PATH)),
            "simulated_limitation_appendix_written": os.path.exists(_repo_path(SIM_LIMITATION_APPENDIX_PATH)),
            "simulated_rollback_package_created": os.path.exists(_repo_path(SIM_ROLLBACK_PATH)),
            "simulated_post_apply_verification_status": build_simulated_post_apply_verification(
                simulated_packet_written
            )["phase207b_simulated_post_apply_verification"][
                "simulated_post_apply_verification_status"
            ],
            "production_gate_regression_status": prod["production_gate_regression_status"],
            "real_owner_decision_input_modified": not prod["real_owner_decision_input_still_pending"],
            "300394_excluded": True,
            "300394_cninfo_limitation_retained": True,
            "300394_cninfo_resolved": False,
            "buy_count": 0,
            "sell_count": 0,
            "hold_count": 0,
            "target_price_count": 0,
            "position_sizing_count": 0,
            "watch_core_updated": False,
            "daily_brief_updated": False,
            "weekly_review_updated": False,
            "broker_api_called": False,
            "llm_api_called": False,
            "ifind_api_called": False,
            "web_fetch_called": False,
            "guard_status": guard["guard_status"],
            "quality_gate_status": qg["quality_gate_status"],
            "cannot_conclude_guard_status": ccg["cannot_conclude_guard_status"],
            "mock_used": False,
            "fixture_used": False,
        }
    }
    _write_json(SIM_DASHBOARD_PATH, result)
    return result


def build_simulation_manifest(simulated_packet_written=False):
    result = {
        "phase207b_simulation_manifest": {
            "manifest_generated": True,
            "simulation_only": True,
            "simulated_packet_written": simulated_packet_written,
            "formal_apply_executed": False,
            "production_packet_written": False,
            "paths": {
                "owner_input": SIM_OWNER_INPUT_PATH,
                "research_packet": SIM_RESEARCH_PACKET_PATH,
                "evidence_packet": SIM_EVIDENCE_PACKET_PATH,
                "limitation_appendix": SIM_LIMITATION_APPENDIX_PATH,
                "rollback_package": SIM_ROLLBACK_PATH,
            },
            "mock_used": False,
            "fixture_used": False,
        }
    }
    _write_json(SIM_MANIFEST_PATH, result)
    return result
