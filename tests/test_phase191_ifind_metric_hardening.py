# Phase191 iFinD metric hardening tests
import unittest, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
from smr_phase191_ifind_metric_hardening import *

class TestMetricHardeningRegistry(unittest.TestCase):
    def test_counts(self):
        r = build_metric_hardening_registry()["phase191_metric_hardening_registry"]
        self.assertEqual(r["total_metrics"], 15)
        self.assertEqual(r["defined_count"], 4)
        self.assertEqual(r["partially_defined_count"], 4)
        self.assertEqual(r["unknown_count"], 7)

    def test_all_have_status_after(self):
        r = build_metric_hardening_registry()["phase191_metric_hardening_registry"]
        for m in r["metrics"]:
            self.assertIn("definition_status_after", m)
            self.assertIn("semantic_category", m)
            self.assertIn("period_type", m)

    def test_no_network(self):
        r = build_metric_hardening_registry()
        self.assertFalse(r["phase191_metric_hardening_registry"]["mock_used"])

class TestSemanticCategoryMap(unittest.TestCase):
    def test_categories(self):
        sc = build_semantic_category_map()["phase191_semantic_category_map"]
        self.assertGreaterEqual(len(sc["categories"]), 6)
        names = [c["name"] for c in sc["categories"]]
        self.assertIn("market_price", names)
        self.assertIn("valuation_multiple", names)
        self.assertIn("unknown", names)

class TestPeriodClassifier(unittest.TestCase):
    def test_all_annual(self):
        pc = build_period_classifier()["phase191_period_classifier"]
        self.assertTrue(pc["all_financial_periods_are_annual"])
        self.assertEqual(pc["unknown_period_count"], 0)

class TestUnitConversionAudit(unittest.TestCase):
    def test_audit_pass(self):
        ua = build_unit_conversion_audit()["phase191_unit_conversion_audit"]
        self.assertEqual(ua["unit_conversion_audit_status"], "pass")
        self.assertEqual(ua["unit_warning_before"], 1)
        self.assertEqual(ua["unit_blocking_count"], 0)

class TestCurrencyChecker(unittest.TestCase):
    def test_all_cny(self):
        cc = build_currency_consistency_checker()["phase191_currency_consistency_checker"]
        self.assertTrue(cc["all_cn_a_consistent_cny"])
        self.assertEqual(cc["currency_mismatch_count"], 0)

class TestBusinessEligibilityGate(unittest.TestCase):
    def test_gate_defined(self):
        bg = build_business_eligibility_gate()["phase191_business_eligibility_gate"]
        self.assertEqual(bg["total_metrics"], 15)
        self.assertTrue(bg["business_use_not_clean_evidence"])
        self.assertTrue(bg["monitoring_use_not_trading_signal"])

    def test_blocked_count(self):
        bg = build_business_eligibility_gate()["phase191_business_eligibility_gate"]
        self.assertGreater(bg["blocked_count"], 0)

class TestWhitelistGraylistBlacklist(unittest.TestCase):
    def test_whitelist(self):
        wl = build_metric_whitelist()["phase191_metric_whitelist"]
        self.assertEqual(wl["whitelist_count"], 4)
        self.assertIn("close_price", wl["whitelist_metrics"])

    def test_graylist(self):
        gl = build_metric_graylist()["phase191_metric_graylist"]
        self.assertEqual(gl["graylist_count"], 4)

    def test_blacklist(self):
        bl = build_metric_blacklist()["phase191_metric_blacklist"]
        self.assertEqual(bl["blacklist_count"], 7)
        self.assertEqual(len(bl["allowed_for"]), 0)

class TestManualConfirmationTemplate(unittest.TestCase):
    def test_template_generated(self):
        mt = build_manual_confirmation_template()["phase191_manual_confirmation_template"]
        self.assertTrue(mt["template_generated"])
        self.assertTrue(mt["do_not_auto_fill"])
        self.assertGreater(mt["items_count"], 0)

class Test300394Eligibility(unittest.TestCase):
    def test_cninfo_retained(self):
        me = build_300394_metric_eligibility()["phase191_300394_metric_eligibility"]
        self.assertTrue(me["cninfo_source_limitation_retained"])
        self.assertTrue(me["coverage_recovery_possible_after_hardening"])
        self.assertFalse(me["actual_coverage_state_updated"])

class TestDailyMonitoringPreview(unittest.TestCase):
    def test_not_actual_update(self):
        dm = build_daily_monitoring_readiness_preview()["phase191_daily_monitoring_readiness_preview"]
        self.assertFalse(dm["actual_daily_monitoring_update"])
        self.assertFalse(dm["watch_core_updated"])
        self.assertTrue(dm["ready_for_phase192_integration"])

class TestMetricDelta(unittest.TestCase):
    def test_delta_generated(self):
        dr = build_metric_delta_report()["phase191_metric_delta_report"]
        self.assertEqual(dr["metric_defined_after"], 4)
        self.assertEqual(dr["metric_unknown_after"], 7)
        self.assertTrue(dr["no_network_calls_made"])

class TestGuard(unittest.TestCase):
    def test_no_api(self):
        g = build_phase191_guard()["phase191_guard"]
        self.assertEqual(g["status"], "pass")
        self.assertFalse(g["ifind_api_called"])
        self.assertFalse(g["network_called"])
        self.assertTrue(g["hardening_not_evidence_creation"])

class TestQualityGate(unittest.TestCase):
    def test_qg_pass(self):
        qg = build_phase191_quality_gate()["phase191_quality_gate"]
        self.assertEqual(qg["status"], "pass")
        self.assertEqual(qg["violations"], 0)
        self.assertTrue(qg["checks"]["no_api_calls"])

class TestCannotConcludeGuard(unittest.TestCase):
    def test_cc_pass(self):
        cc = build_phase191_cannot_conclude_guard()["phase191_cannot_conclude_guard"]
        self.assertEqual(cc["status"], "pass")
        self.assertGreater(len(cc["cannot_conclude"]), 5)

if __name__ == "__main__":
    unittest.main()
