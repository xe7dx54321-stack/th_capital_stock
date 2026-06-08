# Phase189 iFinD capability probe tests
import unittest, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
from smr_phase189_ifind_capability_probe import *

class TestPhase189Config(unittest.TestCase):
    def test_config_loads(self):
        cfg = build_phase189_config()
        self.assertEqual(cfg["phase"], "phase189")
        self.assertIn("ifind_api_capability_probe", cfg["strategy"])
        self.assertTrue(cfg["safety"]["token_never_print"])
        self.assertTrue(cfg["safety"]["token_never_commit"])
        self.assertFalse(cfg["safety"]["mock_allowed"])
        self.assertFalse(cfg["safety"]["real_trade_allowed"])

    def test_config_universe(self):
        cfg = build_phase189_config()
        self.assertEqual(len(cfg["probe"]["cn_a_tickers"]), 4)
        self.assertEqual(len(cfg["probe"]["hk_tickers"]), 2)
        self.assertEqual(len(cfg["probe"]["us_tickers"]), 2)
        self.assertIn("300394.SZ", cfg["probe"]["cn_a_tickers"])

    def test_config_registry(self):
        cfg = build_phase189_config()
        self.assertEqual(cfg["registry"]["source_name"], "ths_ifind_api")
        self.assertEqual(cfg["registry"]["coverage"]["CN_A"], 4)
        self.assertEqual(cfg["registry"]["coverage"]["HK"], 0)

class TestAuthProbe(unittest.TestCase):
    def test_dry_run_skips_network(self):
        result = build_auth_capability_probe(allow_network=False)
        self.assertEqual(result["phase189_auth_capability_probe"]["status"], "skipped")
        self.assertFalse(result["phase189_auth_capability_probe"]["network_called"])

    def test_dry_run_no_token_leak(self):
        result = build_auth_capability_probe(allow_network=False)
        r = result["phase189_auth_capability_probe"]
        self.assertEqual(r["token_masked"], "N/A")

class TestEndpointRegistry(unittest.TestCase):
    def test_registry_defined(self):
        r = build_endpoint_function_registry()
        ep = r["phase189_endpoint_function_registry"]
        self.assertGreater(len(ep["endpoints"]), 0)
        self.assertGreater(len(ep["functions_verified"]["market"]), 0)
        self.assertGreater(len(ep["functions_verified"]["financial"]), 0)

class TestTickerMapper(unittest.TestCase):
    def test_cn_a_mapped(self):
        r = build_cn_a_ticker_mapper()
        m = r["phase189_cn_a_ticker_mapper"]
        self.assertEqual(len(m["mappings"]), 4)
        tickers = [x["ticker"] for x in m["mappings"]]
        self.assertIn("300308.SZ", tickers)
        self.assertIn("300394.SZ", tickers)

    def test_hk_us_not_mapped(self):
        r = build_cn_a_ticker_mapper()
        m = r["phase189_cn_a_ticker_mapper"]
        self.assertTrue(m["hk_us_not_mapped"])

class TestHKUSBoundary(unittest.TestCase):
    def test_boundary_defined(self):
        r = build_hk_us_boundary()
        b = r["phase189_hk_us_boundary"]
        self.assertTrue(b["hk_probe_attempted"])
        self.assertTrue(b["us_probe_attempted"])
        self.assertEqual(b["hk_probe_count"], 2)
        self.assertEqual(b["us_probe_count"], 2)
        self.assertEqual(b["hk_errcode"], -4210)
        self.assertIn("continue", b["hk_us_not_blocked"])

class TestCNACapabilityMatrix(unittest.TestCase):
    def test_dry_run_no_network(self):
        result = build_cn_a_capability_matrix(allow_network=False)
        m = result["phase189_cn_a_capability_matrix"]
        self.assertFalse(m["probe_executed"])
        self.assertFalse(m["network_called"])
        self.assertEqual(m["reason"], "dry_run_or_skip_network")

    def test_dry_run_preserves_tickers(self):
        result = build_cn_a_capability_matrix(allow_network=False)
        m = result["phase189_cn_a_capability_matrix"]
        self.assertEqual(len(m["cn_a_tickers"]), 4)

class TestFieldMapping(unittest.TestCase):
    def test_mappings_exist(self):
        r = build_field_mapping_registry()
        fm = r["phase189_field_mapping_registry"]
        self.assertGreaterEqual(len(fm["mappings"]), 8)

    def test_close_price_mapped(self):
        r = build_field_mapping_registry()
        fm = r["phase189_field_mapping_registry"]
        fields = [x["system_field"] for x in fm["mappings"]]
        self.assertIn("close_price", fields)
        self.assertIn("pe_ttm", fields)
        self.assertIn("revenue", fields)
        self.assertIn("eps_basic", fields)

class TestUnitNormalizer(unittest.TestCase):
    def test_normalizer_defined(self):
        r = build_unit_normalizer()
        un = r["phase189_unit_normalizer"]
        self.assertIn("revenue", un["normalization_rules"])
        self.assertIn("net_profit", un["normalization_rules"])
        self.assertEqual(un["unit_normalization_warnings"], 0)

class TestCurrencyNormalizer(unittest.TestCase):
    def test_cny_only(self):
        r = build_currency_normalizer()
        cn = r["phase189_currency_normalizer"]
        self.assertEqual(cn["cn_a_default_currency"], "CNY")
        self.assertTrue(cn["cn_a_to_hk_us_currency_boundary_enforced"])

class TestPeriodNormalizer(unittest.TestCase):
    def test_period_defined(self):
        r = build_period_normalizer()
        pn = r["phase189_period_normalizer"]
        self.assertEqual(pn["default_report_date"], "20251231")
        self.assertTrue(pn["quarterly_not_probed"])

class TestMetricRegistry(unittest.TestCase):
    def test_metrics_defined(self):
        r = build_metric_definition_registry()
        mr = r["phase189_metric_definition_registry"]
        self.assertEqual(len(mr["defined_metrics"]), 8)
        self.assertGreater(mr["metric_definition_unknown_count"], 0)

class TestSanityChecker(unittest.TestCase):
    def test_checks_pass(self):
        r = build_sanity_checker()
        sc = r["phase189_sanity_checker"]
        self.assertTrue(sc["all_checks_pass"])
        self.assertEqual(sc["warning_count"], 0)

class TestSourceReliability(unittest.TestCase):
    def test_profile_defined(self):
        r = build_source_reliability_profile()
        sr = r["phase189_source_reliability_profile"]
        self.assertEqual(sr["source_tier"], "tier1_professional")
        self.assertEqual(sr["data_provider"], "同花顺iFinD")
        self.assertTrue(sr["reliability_profile_not_trading_advice"])

class TestOutputContract(unittest.TestCase):
    def test_contract_defined(self):
        r = build_output_contract()
        oc = r["phase189_output_contract"]
        self.assertGreaterEqual(len(oc["fields_guaranteed"]), 9)
        self.assertTrue(oc["output_not_clean_evidence"])
        self.assertTrue(oc["output_not_trading_signal"])

class TestErrorClassifier(unittest.TestCase):
    def test_categories_defined(self):
        r = build_error_classifier()
        ec = r["phase189_error_classifier"]
        cats = ec["error_categories"]
        self.assertIn("auth_error", cats)
        self.assertIn("param_error", cats)
        self.assertIn("network_error", cats)

class TestBlockerDowngrade(unittest.TestCase):
    def test_300394_downgraded(self):
        r = build_blocker_downgrade_report()
        bd = r["phase189_blocker_downgrade_report"]
        self.assertEqual(bd["ticker"], "300394.SZ")
        self.assertIn("downgraded", bd["current_blocker_status"])
        self.assertTrue(bd["ifind_recovery"]["market_data_available"])
        self.assertTrue(bd["ifind_recovery"]["financial_data_available"])
        self.assertTrue(bd["ifind_recovery"]["cninfo_limitation_remains"])
        self.assertTrue(bd["downgrade_not_removal"])

    def test_blocker_not_removed(self):
        r = build_blocker_downgrade_report()
        bd = r["phase189_blocker_downgrade_report"]
        self.assertIn("downgraded", bd["current_blocker_status"])
        self.assertNotIn("removed", bd["current_blocker_status"])

class TestGuard(unittest.TestCase):
    def test_guard_pass(self):
        r = build_phase189_guard()
        g = r["phase189_guard"]
        self.assertEqual(g["status"], "pass")
        self.assertTrue(g["token_not_printed"])
        self.assertTrue(g["token_not_committed"])
        self.assertTrue(g["clean_evidence_write_disabled"])
        self.assertTrue(g["llm_api_disabled"])
        self.assertTrue(g["broker_api_disabled"])
        self.assertFalse(g["mock_used"])

class TestQualityGate(unittest.TestCase):
    def test_qg_pass(self):
        r = build_phase189_quality_gate()
        qg = r["phase189_quality_gate"]
        self.assertEqual(qg["status"], "pass")
        self.assertEqual(qg["violations"], 0)
        self.assertTrue(qg["checks"]["no_clean_evidence"])
        self.assertTrue(qg["checks"]["no_token_leak"])

class TestCannotConcludeGuard(unittest.TestCase):
    def test_cc_pass(self):
        r = build_phase189_cannot_conclude_guard()
        cc = r["phase189_cannot_conclude_guard"]
        self.assertEqual(cc["status"], "pass")
        self.assertEqual(cc["violations"], 0)
        self.assertGreater(len(cc["cannot_conclude"]), 0)

    def test_probe_not_ingestion(self):
        r = build_phase189_cannot_conclude_guard()
        cc = r["phase189_cannot_conclude_guard"]
        has_probe_not_ingestion = any("probe_is_not" in x for x in cc["cannot_conclude"])
        self.assertTrue(has_probe_not_ingestion)

class TestBacklog(unittest.TestCase):
    def test_backlog_ready(self):
        r = build_backlog()
        bl = r["phase189_backlog"]
        self.assertTrue(bl["phase189_completed"])
        self.assertTrue(bl["ifind_capability_probe_ready"])
        self.assertTrue(bl["300394_blocker_downgraded"])
        self.assertIn("phase190", bl["next_phases"])

if __name__ == "__main__":
    unittest.main()
