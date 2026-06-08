# Phase193 iFinD daily monitoring bridge tests
import unittest, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
from smr_phase193_ifind_daily_monitoring_bridge import *

class TestBridgeRegistry(unittest.TestCase):
    def test_shadow_only(self):
        r = build_bridge_domain_registry()["phase193_bridge_domain_registry"]
        self.assertTrue(r["shadow_only"])
        self.assertFalse(r["state_write_allowed"])
        self.assertFalse(r["apply_execution_allowed"])
        self.assertTrue(r["bridge_not_state_mutation"])

class TestFieldMapping(unittest.TestCase):
    def test_counts(self):
        fm = build_field_mapping()["phase193_field_mapping"]
        self.assertEqual(fm["total"], 15)
        self.assertEqual(fm["whitelist_mapped"], 4)
        self.assertEqual(fm["graylist_mapped"], 4)
        self.assertEqual(fm["blacklist_excluded"], 7)
    def test_blacklist_not_bridged(self):
        fm = build_field_mapping()["phase193_field_mapping"]
        bl = [m for m in fm["mappings"] if m["metric_list"] == "blacklist"]
        for m in bl:
            self.assertFalse(m["bridge_allowed"])
            self.assertFalse(m.get("included_in_bridge", True))

class TestPolicyCompatibility(unittest.TestCase):
    def test_pass(self):
        p = build_policy_compatibility()["phase193_policy_compatibility"]
        self.assertIn("pass", p["policy_compatibility_status"])
        self.assertTrue(p["policy_not_clean_evidence"])

class TestTickerBridgeMap(unittest.TestCase):
    def test_counts(self):
        tb = build_ticker_bridge_map()["phase193_ticker_bridge_map"]
        self.assertEqual(tb["ticker_count"], 4)
        self.assertTrue(tb["all_bridge_available"])
    def test_300394_limitation(self):
        tb = build_ticker_bridge_map()["phase193_ticker_bridge_map"]
        r394 = [r for r in tb["rows"] if r["ticker"] == "300394.SZ"][0]
        self.assertTrue(r394["cninfo_source_limitation_retained"])
        self.assertFalse(r394["actual_daily_monitoring_state_updated"])

class Test300394BridgeRecovery(unittest.TestCase):
    def test_status(self):
        br = build_300394_bridge_recovery()["phase193_300394_bridge_recovery"]
        self.assertTrue(br["cninfo_source_limitation_retained"])
        self.assertTrue(br["bridge_available"])
        self.assertIn("cninfo_still_limited", br["coverage_recovery_bridge_status"])
        self.assertFalse(br["actual_daily_monitoring_state_updated"])

class TestShadowMonitoring(unittest.TestCase):
    def test_counts(self):
        sh = build_shadow_monitoring_output()["phase193_shadow_monitoring_output"]
        self.assertEqual(sh["shadow_item_count"], 32)
        self.assertEqual(sh["ticker_count"], 4)
        self.assertFalse(sh["actual_state_updated"])
        self.assertFalse(sh["watch_core_updated"])
    def test_all_not_trade_signal(self):
        sh = build_shadow_monitoring_output()["phase193_shadow_monitoring_output"]
        for item in sh["items"]:
            self.assertTrue(item["not_trade_signal"])
            self.assertFalse(item["clean_evidence_created"])

class TestJointPreview(unittest.TestCase):
    def test_no_conflict(self):
        jt = build_joint_monitoring_preview()["phase193_joint_monitoring_preview"]
        self.assertEqual(jt["conflict_detected_count"], 0)
        self.assertEqual(jt["ifind_adds_coverage_count"], 1)

class TestApplyPackage(unittest.TestCase):
    def test_not_executed(self):
        ap = build_apply_package_preview()["phase193_apply_package_preview"]
        self.assertTrue(ap["apply_ready"])
        self.assertFalse(ap["apply_execution_allowed"])
        self.assertTrue(ap["apply_not_executed"])

class TestRollbackPackage(unittest.TestCase):
    def test_not_executed(self):
        rp = build_rollback_package_preview()["phase193_rollback_package_preview"]
        self.assertTrue(rp["rollback_ready"])
        self.assertFalse(rp["rollback_execution_allowed"])

class TestGuard(unittest.TestCase):
    def test_pass(self):
        g = build_phase193_guard()["phase193_guard"]
        self.assertEqual(g["status"], "pass")
        self.assertFalse(g["state_write_allowed"])
        self.assertFalse(g["apply_execution_allowed"])
        self.assertTrue(g["shadow_only"])

class TestQualityGate(unittest.TestCase):
    def test_pass(self):
        q = build_phase193_quality_gate()["phase193_quality_gate"]
        self.assertEqual(q["status"], "pass"); self.assertEqual(q["violations"], 0)

class TestCannotConclude(unittest.TestCase):
    def test_pass(self):
        c = build_phase193_cannot_conclude_guard()["phase193_cannot_conclude_guard"]
        self.assertEqual(c["status"], "pass"); self.assertGreater(len(c["cannot_conclude"]), 5)

if __name__ == "__main__":
    unittest.main()
