# Phase190 iFinD structured CN_A snapshot adapter tests
import unittest, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
from smr_phase190_ifind_structured_snapshot import *

class TestStructuredSnapshots(unittest.TestCase):
    def test_dry_run_snapshots(self):
        snaps = build_structured_snapshots(allow_network=False)
        self.assertEqual(len(snaps), 4)
        for s in snaps:
            self.assertIn(s["ticker"], CN_A_TICKERS)
            self.assertEqual(s["coverage_status"], "dry_run")
            self.assertFalse(s["clean_evidence_created"])
            self.assertTrue(s["not_investment_advice"])

    def test_dry_run_has_cannot_conclude(self):
        snaps = build_structured_snapshots(allow_network=False)
        for s in snaps:
            self.assertIn("cannot_conclude", s)
            self.assertGreater(len(s["cannot_conclude"]), 0)

    def test_dry_run_no_packet_update(self):
        snaps = build_structured_snapshots(allow_network=False)
        for s in snaps:
            self.assertFalse(s["packet_updated"])
            self.assertFalse(s["daily_brief_updated"])

class TestMetricHardening(unittest.TestCase):
    def test_counts(self):
        mh = build_metric_hardening()
        m = mh["phase190_metric_hardening"]
        self.assertEqual(m["defined_count"], 8)
        self.assertEqual(m["partially_defined_count"], 4)
        self.assertEqual(m["unknown_count"], 7)
        self.assertEqual(m["manual_review_required_count"], 4)

    def test_partially_defined_not_business_safe(self):
        mh = build_metric_hardening()
        m = mh["phase190_metric_hardening"]
        for metric in m["defined_metrics"]:
            if metric["definition_status"] == "partially_defined":
                self.assertFalse(metric["safe_for_business_use"])
                self.assertTrue(metric["manual_confirmation_required"])

    def test_unknown_not_business_safe(self):
        mh = build_metric_hardening()
        m = mh["phase190_metric_hardening"]
        for metric in m["unknown_metrics"]:
            self.assertFalse(metric["safe_for_business_use"])

class TestUnitSanity(unittest.TestCase):
    def test_mixed_unit_detected(self):
        us = build_unit_sanity_report()
        u = us["phase190_unit_sanity_report"]
        self.assertTrue(u["mixed_unit_detected"])
        self.assertEqual(u["unit_sanity_warning_count"], 1)
        self.assertTrue(u["business_use_allowed"])

class TestSnapshotSanityChecker(unittest.TestCase):
    def test_dry_run_sanity(self):
        snaps = build_structured_snapshots(allow_network=False)
        sc = build_snapshot_sanity_checker(snaps)
        s = sc["phase190_snapshot_sanity_checker"]
        self.assertEqual(s["total_checked"], 4)
        self.assertTrue(s["sanity_not_clean_evidence"])

class TestCrossSourcePreview(unittest.TestCase):
    def test_preview_generated(self):
        cs = build_cross_source_comparison_preview()
        c = cs["phase190_cross_source_comparison_preview"]
        self.assertTrue(c["comparison_not_verified_evidence"])
        self.assertEqual(len(c["ifind_vs_existing"]), 4)

class TestCoverageRecovery(unittest.TestCase):
    def test_300394_recovery_preview(self):
        cr = build_300394_coverage_recovery_preview()
        c = cr["phase190_300394_coverage_recovery_preview"]
        self.assertEqual(c["ticker"], "300394.SZ")
        self.assertTrue(c["cninfo_source_limitation"])
        self.assertTrue(c["recovery_not_full_coverage_restoration"])
        self.assertTrue(c["cninfo_blocker_not_removed"])

    def test_ifind_coverage_fields(self):
        cr = build_300394_coverage_recovery_preview()
        c = cr["phase190_300394_coverage_recovery_preview"]
        ic = c["ifind_coverage"]
        self.assertTrue(ic["quote_available"])
        self.assertTrue(ic["financial_available"])
        self.assertTrue(ic["structured_snapshot_generated"])

class TestDailyMonitoringPreview(unittest.TestCase):
    def test_preview_generated(self):
        dm = build_daily_monitoring_preview()
        d = dm["phase190_daily_monitoring_preview"]
        self.assertEqual(len(d["ready_tickers"]), 4)
        self.assertTrue(d["daily_monitoring_not_updated"])
        self.assertGreater(len(d["prerequisites_pending"]), 0)

class TestGuard(unittest.TestCase):
    def test_guard_pass(self):
        g = build_phase190_guard()
        gg = g["phase190_guard"]
        self.assertEqual(gg["status"], "pass")
        self.assertTrue(gg["clean_evidence_write_disabled"])
        self.assertTrue(gg["daily_monitoring_update_disabled"])
        self.assertTrue(gg["watch_core_update_disabled"])
        self.assertFalse(gg["mock_used"])

class TestQualityGate(unittest.TestCase):
    def test_qg_pass(self):
        qg = build_phase190_quality_gate()
        q = qg["phase190_quality_gate"]
        self.assertEqual(q["status"], "pass")
        self.assertEqual(q["violations"], 0)

class TestCannotConcludeGuard(unittest.TestCase):
    def test_cc_pass(self):
        cc = build_phase190_cannot_conclude_guard()
        c = cc["phase190_cannot_conclude_guard"]
        self.assertEqual(c["status"], "pass")
        self.assertEqual(c["violations"], 0)
        self.assertGreater(len(c["cannot_conclude"]), 5)

class TestBacklog(unittest.TestCase):
    def test_backlog_ready(self):
        bl = build_backlog()
        b = bl["phase190_backlog"]
        self.assertTrue(b["phase190_completed"])
        self.assertTrue(b["structured_snapshot_ready"])
        self.assertTrue(b["300394_coverage_recovery_preview_ready"])

if __name__ == "__main__":
    unittest.main()
