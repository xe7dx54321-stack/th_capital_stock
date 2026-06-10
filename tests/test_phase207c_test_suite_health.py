import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))

from smr_phase207c_test_suite_health import (
    LEGACY_TEST_FILE,
    build_additive_source_audit,
    build_dashboard,
    build_legacy_import_debt_report,
    build_phase207c_config,
    build_production_safety_regression,
    build_test_inventory,
    build_test_profiles,
    build_timeout_triage_report,
    run_phase207c,
)


class Phase207cTestSuiteHealthTest(unittest.TestCase):
    def test_config_disables_formal_apply_and_trade_outputs(self):
        config = build_phase207c_config()["phase207c_config"]
        self.assertTrue(config["research_only"])
        self.assertFalse(config["formal_apply_execution_allowed"])
        self.assertFalse(config["watch_core_update_allowed"])
        self.assertFalse(config["trade_recommendation_allowed"])
        self.assertFalse(config["target_price_output_allowed"])
        self.assertFalse(config["position_sizing_allowed"])

    def test_inventory_detects_tests_and_legacy_candidate(self):
        inventory = build_test_inventory(write=False)["phase207c_test_inventory"]
        self.assertGreater(inventory["test_file_count"], 1000)
        self.assertIn(LEGACY_TEST_FILE, inventory["legacy_test_files"])
        self.assertEqual(inventory["legacy_import_debt_candidate"], LEGACY_TEST_FILE)

    def test_profiles_define_required_layers(self):
        profiles = build_test_profiles(write=False)["phase207c_test_profiles"]["profiles"]
        self.assertEqual(set(profiles), {"fast", "regression", "evidence-chain", "apply-gate", "full-diagnostic"})
        self.assertFalse(profiles["full-diagnostic"]["hard_gate"])

    def test_execute_builds_dashboard_without_formal_apply(self):
        result = run_phase207c(mode="dry-run")["phase207c_test_suite_health"]
        self.assertTrue(result["phase207c_enabled"])
        self.assertTrue(result["test_inventory_created"])
        self.assertFalse(result["formal_apply_executed"])
        self.assertFalse(result["production_packet_written"])
        self.assertTrue(result["production_gate_still_fail_closed"])

    def test_timeout_report_is_diagnostic_not_pass(self):
        report = build_timeout_triage_report(write=False)["phase207c_timeout_triage_report"]
        self.assertTrue(report["timed_out"])
        self.assertEqual(report["full_diagnostic_status"], "timeout_diagnostic")

    def test_additive_source_policy_preserved(self):
        audit = build_additive_source_audit(write=False)["phase207c_additive_source_audit"]
        self.assertTrue(audit["ifind_additional_source_only"])
        self.assertFalse(audit["ifind_replacement_detected"])
        self.assertTrue(audit["existing_sources_preserved"])

    def test_production_safety_remains_fail_closed(self):
        safety = build_production_safety_regression(write=False)["phase207c_production_safety_regression"]
        self.assertTrue(safety["real_owner_input_pending"])
        self.assertTrue(safety["production_gate_still_fail_closed"])
        self.assertFalse(safety["formal_apply_executed"])

    def test_dashboard_has_required_fields(self):
        run_phase207c(mode="execute")
        dashboard = build_dashboard(write=False)["phase207c_dashboard"]
        self.assertEqual(dashboard["fast_profile_status"], "pass")
        self.assertEqual(dashboard["regression_profile_status"], "pass")
        self.assertEqual(dashboard["evidence_chain_profile_status"], "pass")
        self.assertEqual(dashboard["apply_gate_profile_status"], "pass")


if __name__ == "__main__":
    unittest.main()
