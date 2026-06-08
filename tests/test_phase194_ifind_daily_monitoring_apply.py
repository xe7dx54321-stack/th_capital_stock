# Phase194 iFinD daily monitoring apply tests
import unittest, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
from smr_phase194_ifind_daily_monitoring_apply import *

class TestApplyPrerequisiteChecker(unittest.TestCase):
    def test_all_pass(self):
        p = build_apply_prerequisite_checker()["phase194_apply_prerequisite_checker"]
        self.assertTrue(p["all_pass"]); self.assertTrue(p["can_apply"])

class TestExplicitApplyGate(unittest.TestCase):
    def test_no_flag_no_apply(self):
        g = build_explicit_apply_gate(False)["phase194_explicit_apply_gate"]
        self.assertFalse(g["can_apply"]); self.assertFalse(g["applied"])
        self.assertFalse(g["state_write_allowed"])
    def test_with_flag_can_apply(self):
        g = build_explicit_apply_gate(True)["phase194_explicit_apply_gate"]
        self.assertTrue(g["can_apply"])
        self.assertTrue(g["state_write_allowed"])
        self.assertTrue(g["watch_core_write_disabled"])

class TestDailyMonitoringState(unittest.TestCase):
    def test_no_flag_no_write(self):
        s = build_daily_monitoring_state(False)["phase194_daily_monitoring_state"]
        self.assertFalse(s["state_written"])
    def test_with_flag_write(self):
        s = build_daily_monitoring_state(True)["phase194_daily_monitoring_state"]
        self.assertTrue(s["state_written"])
        self.assertEqual(s["ticker_count"], 4)
        self.assertEqual(s["metric_count"], 32)
        self.assertTrue(s["graylist_policy_preserved"])
        self.assertTrue(s["blacklist_exclusion_preserved"])
        self.assertTrue(s["cninfo_limitations_retained"])
        self.assertFalse(s["watch_core_updated"])
        self.assertFalse(s["clean_evidence_created"])
    def test_graylist_manual_confirmation(self):
        s = build_daily_monitoring_state(True)["phase194_daily_monitoring_state"]
        gl = [m for m in s["metrics"] if m["metric_list_status"] == "graylist"]
        for m in gl:
            self.assertTrue(m["manual_confirmation_required"])
            self.assertIn("requires_manual_confirmation", str(m["cannot_conclude"]))
    def test_all_clean_evidence_false(self):
        s = build_daily_monitoring_state(True)["phase194_daily_monitoring_state"]
        for m in s["metrics"]:
            self.assertFalse(m["clean_evidence_created"])
            self.assertFalse(m["trade_signal_created"])

class TestStateDiff(unittest.TestCase):
    def test_generated(self):
        d = build_state_diff()["phase194_state_diff"]
        self.assertTrue(d["diff_generated"]); self.assertEqual(d["ifind_additions"]["metrics_added"], 32)

class TestCommitManifest(unittest.TestCase):
    def test_no_apply_no_commit(self):
        c = build_commit_manifest(False)["phase194_commit_manifest"]
        self.assertFalse(c["committed"]); self.assertIsNone(c["commit_id"])
    def test_apply_commits(self):
        c = build_commit_manifest(True)["phase194_commit_manifest"]
        self.assertTrue(c["committed"]); self.assertIsNotNone(c["commit_id"])

class Test300394StateCommit(unittest.TestCase):
    def test_no_apply_not_committed(self):
        s = build_300394_state_commit(False)["phase194_300394_state_commit"]
        self.assertFalse(s["state_committed"]); self.assertTrue(s["cninfo_source_limitation_retained"])
    def test_apply_committed(self):
        s = build_300394_state_commit(True)["phase194_300394_state_commit"]
        self.assertTrue(s["state_committed"]); self.assertIn("committed", s["coverage_recovery_status"])

class TestBlacklistVerifier(unittest.TestCase):
    def test_zero_in_state(self):
        b = build_blacklist_exclusion_verifier()["phase194_blacklist_exclusion_verifier"]
        self.assertEqual(b["blacklist_in_state_count"], 0); self.assertTrue(b["verification_passed"])

class TestGuard(unittest.TestCase):
    def test_pass(self):
        g = build_phase194_guard()["phase194_guard"]
        self.assertEqual(g["status"], "pass"); self.assertTrue(g["watch_core_write_disabled"])

class TestQualityGate(unittest.TestCase):
    def test_pass(self):
        q = build_phase194_quality_gate()["phase194_quality_gate"]
        self.assertEqual(q["status"], "pass"); self.assertEqual(q["violations"], 0)

class TestCannotConclude(unittest.TestCase):
    def test_pass(self):
        c = build_phase194_cannot_conclude_guard()["phase194_cannot_conclude_guard"]
        self.assertEqual(c["status"], "pass"); self.assertGreater(len(c["cannot_conclude"]), 5)

if __name__ == "__main__":
    unittest.main()
