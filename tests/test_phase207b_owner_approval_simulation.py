import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))

from smr_phase207b_owner_approval_simulation import (
    REAL_OWNER_INPUT_PATH,
    SIM_EVIDENCE_PACKET_PATH,
    SIM_LIMITATION_APPENDIX_PATH,
    SIM_OWNER_INPUT_PATH,
    SIM_RESEARCH_PACKET_PATH,
    SIM_ROLLBACK_PATH,
    build_additive_source_audit,
    build_artifact_loaders,
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
    build_simulation_validator,
)


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def full_path(path):
    return os.path.join(ROOT, path)


class Phase207bSimulationTest(unittest.TestCase):
    def test_config_is_simulation_only(self):
        result = build_phase207b_config()["phase207b_config"]
        self.assertTrue(result["simulation_only"])
        self.assertFalse(result["production_packet_write_allowed"])

    def test_artifacts_loaded_and_real_owner_pending(self):
        result = build_artifact_loaders()["phase207b_artifact_loaders"]
        self.assertTrue(result["phase207_loaded"])
        self.assertTrue(result["phase206_loaded"])
        self.assertTrue(result["phase205_loaded"])
        self.assertTrue(result["real_owner_decision_input_still_pending"])

    def test_simulated_owner_input_can_generate(self):
        result = build_simulated_owner_input(generate=True)["phase207b_simulated_owner_input"]
        self.assertTrue(result["simulated_owner_input_created"])
        self.assertTrue(result["simulation_only"])
        self.assertTrue(result["not_real_owner_approval"])

    def test_simulated_owner_input_does_not_modify_real_input(self):
        build_simulated_owner_input(generate=True)
        with open(full_path(REAL_OWNER_INPUT_PATH), "r", encoding="utf-8") as handle:
            real_input = json.load(handle)
        self.assertEqual(real_input["owner_confirmation"], "PENDING_OWNER_FILL")
        self.assertEqual(real_input["owner_notes"], "PENDING_OWNER_NOTES")

    def test_simulation_validator_passes(self):
        build_simulated_owner_input(generate=True)
        result = build_simulation_validator()["phase207b_simulation_validator"]
        self.assertTrue(result["simulated_owner_decision_valid"])

    def test_production_gate_stays_fail_closed(self):
        result = build_production_gate_regression()["phase207b_production_gate_regression"]
        self.assertEqual(result["production_gate_regression_status"], "pass")
        self.assertFalse(result["production_phase207_can_execute"])
        self.assertFalse(result["production_formal_apply_executed"])
        self.assertFalse(result["production_packet_written"])

    def test_simulated_apply_scope_is_7_of_8(self):
        result = build_simulated_apply_scope()["phase207b_simulated_apply_scope"]
        self.assertEqual(result["included_ticker_count"], 7)
        self.assertEqual(result["excluded_ticker_count"], 1)
        self.assertEqual(result["excluded_tickers"], ["300394.SZ"])
        self.assertTrue(result["300394_excluded"])
        self.assertFalse(result["300394_cninfo_resolved"])

    def test_simulation_gate_requires_simulation_request(self):
        build_simulated_owner_input(generate=True)
        result = build_simulation_apply_gate(simulate_apply=False)["phase207b_simulation_apply_gate"]
        self.assertFalse(result["can_simulate_apply"])

    def test_simulated_packet_writer_writes_only_in_write_mode(self):
        build_simulated_owner_input(generate=True)
        result = build_simulated_packet_writer(
            simulate_apply=True,
            write_simulated_packet=True,
        )["phase207b_simulated_packet_writer"]
        self.assertTrue(result["simulated_packet_written"])
        self.assertTrue(result["simulated_research_packet_written"])
        self.assertTrue(result["simulated_evidence_packet_written"])
        self.assertTrue(result["simulated_limitation_appendix_written"])
        self.assertTrue(result["simulated_rollback_package_created"])
        self.assertFalse(result["formal_apply_executed"])
        self.assertFalse(result["production_packet_written"])

    def test_simulated_files_written_to_simulation_path(self):
        build_simulated_owner_input(generate=True)
        build_simulated_packet_writer(simulate_apply=True, write_simulated_packet=True)
        for path in [
            SIM_OWNER_INPUT_PATH,
            SIM_RESEARCH_PACKET_PATH,
            SIM_EVIDENCE_PACKET_PATH,
            SIM_LIMITATION_APPENDIX_PATH,
            SIM_ROLLBACK_PATH,
        ]:
            self.assertTrue(os.path.exists(full_path(path)))

    def test_post_apply_verification_passes_after_write(self):
        build_simulated_owner_input(generate=True)
        build_simulated_packet_writer(simulate_apply=True, write_simulated_packet=True)
        result = build_simulated_post_apply_verification(True)[
            "phase207b_simulated_post_apply_verification"
        ]
        self.assertEqual(result["simulated_post_apply_verification_status"], "pass")
        self.assertFalse(result["checks"]["production_packet_written"])
        self.assertFalse(result["checks"]["300394_cninfo_resolved"])

    def test_additive_source_audit_passes(self):
        result = build_additive_source_audit()["phase207b_additive_source_audit"]
        self.assertTrue(result["ifind_additional_source_only"])
        self.assertFalse(result["ifind_replacement_detected"])
        self.assertTrue(result["existing_sources_preserved"])
        self.assertTrue(result["existing_adapters_preserved"])
        self.assertTrue(result["existing_routes_preserved"])

    def test_guard_passes(self):
        result = build_safety_guard(True)["phase207b_safety_guard"]
        self.assertEqual(result["guard_status"], "pass")
        self.assertEqual(result["violations_count"], 0)
        self.assertFalse(result["formal_apply_executed"])
        self.assertFalse(result["production_packet_written"])

    def test_quality_gate_passes(self):
        build_simulated_owner_input(generate=True)
        build_simulated_apply_scope()
        build_simulated_packet_writer(simulate_apply=True, write_simulated_packet=True)
        result = build_quality_gate(True)["phase207b_quality_gate"]
        self.assertEqual(result["quality_gate_status"], "pass")
        self.assertEqual(result["violations_count"], 0)

    def test_cannot_conclude_guard_passes(self):
        result = build_cannot_conclude_guard()["phase207b_cannot_conclude_guard"]
        self.assertEqual(result["cannot_conclude_guard_status"], "pass")
        self.assertEqual(result["violations_count"], 0)

    def test_dashboard_contains_required_safety_fields(self):
        build_simulated_owner_input(generate=True)
        build_simulated_packet_writer(simulate_apply=True, write_simulated_packet=True)
        result = build_dashboard(True)["phase207b_dashboard"]
        self.assertTrue(result["simulation_only"])
        self.assertTrue(result["not_real_owner_approval"])
        self.assertTrue(result["simulated_formal_apply_executed"])
        self.assertFalse(result["formal_apply_executed"])
        self.assertFalse(result["production_packet_written"])
        self.assertEqual(result["buy_count"], 0)
        self.assertEqual(result["sell_count"], 0)
        self.assertEqual(result["hold_count"], 0)
        self.assertEqual(result["target_price_count"], 0)
        self.assertEqual(result["position_sizing_count"], 0)
        self.assertEqual(result["guard_status"], "pass")
        self.assertEqual(result["quality_gate_status"], "pass")
        self.assertEqual(result["cannot_conclude_guard_status"], "pass")


if __name__ == "__main__":
    unittest.main()
