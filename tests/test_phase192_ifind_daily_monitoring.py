# Phase192 iFinD daily monitoring tests
import unittest, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
from smr_phase192_ifind_daily_monitoring import *

class TestMonitoringDomainRegistry(unittest.TestCase):
    def test_registry(self):
        r = build_monitoring_domain_registry()["phase192_monitoring_domain_registry"]
        self.assertTrue(r["registry_defined"])
        self.assertEqual(r["cn_a_tickers"], CN_A_TICKERS)
        self.assertTrue(r["hk_us_disabled"])
        self.assertTrue(r["monitoring_not_trading"])

class TestMonitoringMetricManifest(unittest.TestCase):
    def setUp(self):
        self.snaps = build_monitoring_snapshots(allow_network=False)
    def test_manifest_structure(self):
        m = build_monitoring_metric_manifest(self.snaps)["phase192_monitoring_metric_manifest"]
        self.assertGreater(m["total_metrics"], 0)
        self.assertEqual(m["whitelist_metric_count"], 16)
        self.assertEqual(m["graylist_metric_count"], 16)
        self.assertGreater(m["blacklist_excluded_count"], 0)
    def test_all_rows_have_clean_evidence_false(self):
        m = build_monitoring_metric_manifest(self.snaps)["phase192_monitoring_metric_manifest"]
        for r in m["rows"]:
            self.assertFalse(r["clean_evidence_created"])
            self.assertFalse(r["trade_signal_created"])
    def test_graylist_manual_confirmation(self):
        m = build_monitoring_metric_manifest(self.snaps)["phase192_monitoring_metric_manifest"]
        gl = [r for r in m["rows"] if r["metric_list"]=="graylist"]
        for r in gl:
            self.assertTrue(r["manual_confirmation_required"])

class TestFreshness(unittest.TestCase):
    def test_fresh(self):
        f = build_freshness_checker()["phase192_freshness_checker"]
        self.assertEqual(f["freshness_status"], "all_fresh_or_within_window")
        self.assertTrue(f["fresh_not_verified_evidence"])

class TestBaselineDelta(unittest.TestCase):
    def setUp(self):
        self.snaps = build_monitoring_snapshots(allow_network=False)
    def test_first_run_baseline(self):
        d = build_baseline_delta_preview(self.snaps)["phase192_baseline_delta_preview"]
        self.assertTrue(d["first_run_baseline"])
        self.assertTrue(d["delta_preview_not_investment_signal"])

class TestQualityClassifier(unittest.TestCase):
    def test_counts(self):
        q = build_quality_status_classifier()["phase192_quality_status_classifier"]
        self.assertEqual(q["monitoring_ready"], 4)
        self.assertEqual(q["monitoring_ready_with_confirmation"], 4)
        self.assertEqual(q["blocked"], 7)

class Test300394Lane(unittest.TestCase):
    def setUp(self):
        self.snaps = build_monitoring_snapshots(allow_network=False)
    def test_cninfo_retained(self):
        l = build_300394_monitoring_recovery_lane(self.snaps)["phase192_300394_monitoring_recovery_lane"]
        self.assertTrue(l["cninfo_source_limitation_retained"])
        self.assertFalse(l["actual_watch_core_updated"])
        self.assertFalse(l["actual_daily_monitoring_state_updated"])

class TestBridgePreview(unittest.TestCase):
    def test_not_executed(self):
        b = build_daily_monitoring_bridge_preview()["phase192_daily_monitoring_bridge_preview"]
        self.assertFalse(b["actual_integration_executed"])
        self.assertTrue(b["watch_core_not_updated"])

class TestGuard(unittest.TestCase):
    def test_pass(self):
        g = build_phase192_guard()["phase192_guard"]
        self.assertEqual(g["status"], "pass")
        self.assertTrue(g["daily_monitoring_state_update_disabled"])
        self.assertTrue(g["watch_core_update_disabled"])

class TestQualityGate(unittest.TestCase):
    def test_pass(self):
        q = build_phase192_quality_gate()["phase192_quality_gate"]
        self.assertEqual(q["status"], "pass"); self.assertEqual(q["violations"], 0)

class TestCannotConclude(unittest.TestCase):
    def test_pass(self):
        c = build_phase192_cannot_conclude_guard()["phase192_cannot_conclude_guard"]
        self.assertEqual(c["status"], "pass"); self.assertGreater(len(c["cannot_conclude"]), 5)

if __name__ == "__main__":
    unittest.main()
