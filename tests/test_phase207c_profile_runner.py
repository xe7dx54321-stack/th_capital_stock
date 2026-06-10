import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))

from smr_phase207c_test_suite_health import run_profile, selected_files_for_profile


class Phase207cProfileRunnerTest(unittest.TestCase):
    def test_fast_profile_passes(self):
        result = run_profile("fast", write=False)["phase207c_profile_runner"]
        self.assertEqual(result["profile_status"], "pass")
        self.assertGreater(result["tests_run"], 0)

    def test_apply_gate_profile_passes(self):
        result = run_profile("apply-gate", write=False)["phase207c_profile_runner"]
        self.assertEqual(result["profile_status"], "pass")
        self.assertGreaterEqual(result["tests_run"], 74)

    def test_regression_profile_selects_phase20_family(self):
        files = selected_files_for_profile("regression")
        self.assertIn("tests/test_phase207b_owner_approval_simulation.py", files)
        self.assertTrue(all("test_phase20" in file for file in files))

    def test_full_diagnostic_is_timeout_diagnostic_report_only(self):
        result = run_profile("full-diagnostic", timeout_seconds=1, write=False, run_full=False)["phase207c_profile_runner"]
        self.assertEqual(result["profile_status"], "timeout_diagnostic")
        self.assertTrue(result["timed_out"])


if __name__ == "__main__":
    unittest.main()
