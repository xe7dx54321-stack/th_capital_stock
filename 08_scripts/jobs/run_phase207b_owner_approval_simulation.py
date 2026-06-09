import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from smr_phase207b_owner_approval_simulation import (
    build_additive_source_audit,
    build_artifact_loaders,
    build_backlog_update,
    build_cannot_conclude_guard,
    build_dashboard,
    build_phase207b_config,
    build_production_gate_regression,
    build_quality_gate,
    build_safety_guard,
    build_simulated_apply_scope,
    build_simulated_owner_input,
    build_simulated_packet_writer,
    build_simulated_post_apply_verification,
    build_simulation_apply_gate,
    build_simulation_board,
    build_simulation_brief,
    build_simulation_manifest,
    build_simulation_validator,
)


def run():
    execute = "--execute" in sys.argv
    dry_run = "--dry-run" in sys.argv
    skip_network = "--skip-network" in sys.argv
    generate_input = "--generate-simulated-owner-input" in sys.argv
    simulate_apply = "--simulate-apply" in sys.argv
    write_packet = "--write-simulated-packet" in sys.argv

    if execute and simulate_apply and write_packet:
        mode = "write-simulated-packet"
    elif execute and simulate_apply:
        mode = "simulate-apply"
    elif execute and generate_input:
        mode = "generate-simulated-owner-input"
    elif execute:
        mode = "execute"
    elif skip_network:
        mode = "skip-network"
    elif dry_run:
        mode = "dry-run"
    else:
        mode = "dry-run"

    build_phase207b_config()
    build_artifact_loaders()
    build_simulated_owner_input(generate=execute and generate_input)
    if simulate_apply:
        build_simulated_apply_scope()
    validator = build_simulation_validator()
    build_simulation_apply_gate(simulate_apply=simulate_apply)
    writer = build_simulated_packet_writer(
        simulate_apply=simulate_apply,
        write_simulated_packet=write_packet,
    )
    simulated_written = writer["phase207b_simulated_packet_writer"]["simulated_packet_written"]
    post_apply = build_simulated_post_apply_verification(simulated_written)
    prod = build_production_gate_regression()
    audit = build_additive_source_audit()
    guard = build_safety_guard(simulated_written)
    ccg = build_cannot_conclude_guard()
    quality = build_quality_gate(simulated_written)
    build_simulation_board()
    build_simulation_brief()
    build_simulation_manifest(simulated_written)
    build_backlog_update()
    dashboard = build_dashboard(simulated_written)

    summary = {
        "phase207b_owner_approval_simulation": {
            "mode": mode,
            "simulated_owner_input_created": dashboard["phase207b_dashboard"][
                "simulated_owner_input_created"
            ],
            "simulation_only": True,
            "not_real_owner_approval": True,
            "real_owner_input_still_pending": prod["phase207b_production_gate_regression"][
                "real_owner_decision_input_still_pending"
            ],
            "production_gate_still_fail_closed": prod["phase207b_production_gate_regression"][
                "production_gate_regression_status"
            ]
            == "pass",
            "simulated_owner_decision_valid": validator["phase207b_simulation_validator"][
                "simulated_owner_decision_valid"
            ],
            "included_ticker_count": 7,
            "excluded_ticker_count": 1,
            "excluded_tickers": ["300394.SZ"],
            "300394_excluded": True,
            "300394_cninfo_limitation_retained": True,
            "300394_cninfo_resolved": False,
            "simulated_formal_apply_executed": simulated_written,
            "formal_apply_executed": False,
            "production_packet_written": False,
            "simulated_packet_written": simulated_written,
            "simulated_research_packet_written": writer["phase207b_simulated_packet_writer"][
                "simulated_research_packet_written"
            ],
            "simulated_evidence_packet_written": writer["phase207b_simulated_packet_writer"][
                "simulated_evidence_packet_written"
            ],
            "simulated_limitation_appendix_written": writer[
                "phase207b_simulated_packet_writer"
            ]["simulated_limitation_appendix_written"],
            "simulated_rollback_package_created": writer["phase207b_simulated_packet_writer"][
                "simulated_rollback_package_created"
            ],
            "simulated_post_apply_verification_status": post_apply[
                "phase207b_simulated_post_apply_verification"
            ]["simulated_post_apply_verification_status"],
            "watch_core_updated": False,
            "daily_brief_updated": False,
            "weekly_review_updated": False,
            "buy_count": 0,
            "sell_count": 0,
            "hold_count": 0,
            "target_price_count": 0,
            "position_sizing_count": 0,
            "broker_api_called": False,
            "llm_api_called": False,
            "ifind_api_called": False,
            "web_fetch_called": False,
            "ifind_additional_source_only": audit["phase207b_additive_source_audit"][
                "ifind_additional_source_only"
            ],
            "ifind_replacement_detected": False,
            "existing_sources_preserved": True,
            "existing_adapters_preserved": True,
            "guard_status": guard["phase207b_safety_guard"]["guard_status"],
            "quality_gate_status": quality["phase207b_quality_gate"]["quality_gate_status"],
            "cannot_conclude_guard_status": ccg["phase207b_cannot_conclude_guard"][
                "cannot_conclude_guard_status"
            ],
            "mock_used": False,
            "fixture_used": False,
        }
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run()
