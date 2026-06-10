import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))

from smr_phase207c_test_suite_health import (
    build_cannot_conclude_guard,
    build_quality_gate,
    build_safety_guard,
    run_phase207c,
)


class Phase207cGuardTest(unittest.TestCase):
    def test_safety_guard_passes(self):
        run_phase207c(mode="dry-run")
        guard = build_safety_guard(write=False)["phase207c_safety_guard"]
        self.assertEqual(guard["guard_status"], "pass")
        self.assertEqual(guard["violations_count"], 0)
        self.assertFalse(guard["formal_apply_executed"])
        self.assertFalse(guard["production_packet_written"])

    def test_quality_gate_passes_with_full_diagnostic_warning(self):
        run_phase207c(mode="execute")
        gate = build_quality_gate(write=False)["phase207c_quality_gate"]
        self.assertIn(gate["quality_gate_status"], ["pass", "pass_with_warning"])
        self.assertTrue(gate["full_diagnostic_timeout"])
        self.assertEqual(gate["violations_count"], 0)

    def test_cannot_conclude_guard_passes(self):
        guard = build_cannot_conclude_guard(write=False)["phase207c_cannot_conclude_guard"]
        self.assertEqual(guard["cannot_conclude_guard_status"], "pass")
        self.assertEqual(guard["violations_count"], 0)


if __name__ == "__main__":
    unittest.main()
