# Tests for Phase197 CN_A Web Scout Expansion
import json, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase197_cn_a_web_scout_expansion import (
    build_phase197_config, build_domain_registry, build_source_universe,
    build_official_source_routes, build_company_ir_routes,
    build_investor_interaction_routes, build_financial_news_routes,
    build_query_plan, build_safe_network_policy, build_fetch_status,
    build_source_lead_observations, build_source_category_classifier,
    build_source_reliability_pre_score, build_dedup, build_dirty_inbox_converter,
    build_ingestion_manifest, build_same_market_alignment_preview,
    build_phase196_rerun_readiness, build_next_verification_task_seed,
    build_blocked_source_handler, build_scout_board, build_scout_brief,
    build_backlog_update, build_cannot_conclude_guard, build_quality_gate,
    build_dashboard, CN_A_SCOUT_TICKERS, CN_A_SOURCE_CATEGORIES
)

class TestPhase197Config(unittest.TestCase):
    def test_config(self):
        r = build_phase197_config()["phase197_config"]
        self.assertTrue(r["config_loaded"])
        self.assertEqual(r["phase"], "phase197")
        self.assertEqual(r["cn_a_ticker_count"], 4)
    def test_safety(self):
        r = build_phase197_config()["phase197_config"]
        self.assertTrue(r["clean_evidence_disabled"])
        self.assertFalse(r["mock_used"])

class TestPhase197DomainRegistry(unittest.TestCase):
    def test_registry(self):
        r = build_domain_registry()["phase197_domain_registry"]
        self.assertTrue(r["registry_defined"])
        self.assertEqual(r["domain_count"], 6)
        self.assertTrue(r["all_cn_a"])

class TestPhase197SourceUniverse(unittest.TestCase):
    def test_universe(self):
        r = build_source_universe()["phase197_source_universe"]
        self.assertEqual(r["tickers_total"], 4)
        self.assertEqual(r["cn_a_web_scout_enabled"], 4)
        self.assertEqual(r["blocked"], 1)

class TestPhase197SourceRoutes(unittest.TestCase):
    def test_official(self):
        r = build_official_source_routes()["phase197_official_source_routes"]
        self.assertGreater(r["route_count"], 0)
    def test_ir(self):
        r = build_company_ir_routes()["phase197_company_ir_routes"]
        self.assertEqual(r["route_count"], 4)
    def test_investor(self):
        r = build_investor_interaction_routes()["phase197_investor_interaction_routes"]
        self.assertEqual(r["route_count"], 4)
    def test_news(self):
        r = build_financial_news_routes()["phase197_financial_news_routes"]
        self.assertEqual(r["route_count"], 8)

class TestPhase197QueryPlan(unittest.TestCase):
    def test_plan(self):
        r = build_query_plan(False)["phase197_query_plan"]
        self.assertTrue(r["plan_defined"])
        self.assertGreater(r["query_count"], 0)
        self.assertTrue(r["dry_run"])
    def test_execute(self):
        r = build_query_plan(True)["phase197_query_plan"]
        self.assertTrue(r["network_called"])

class TestPhase197FetchStatus(unittest.TestCase):
    def test_fetch(self):
        r = build_fetch_status(True)["phase197_fetch_status"]
        self.assertGreater(r["fetch_attempts"], 0)
        self.assertIn("fetched", r["status_summary"])

class TestPhase197SourceLeads(unittest.TestCase):
    def test_leads(self):
        r = build_source_lead_observations(True)["phase197_source_leads"]
        self.assertGreater(r["lead_count"], 0)
        self.assertTrue(r["all_leads_not_clean_evidence"])
        self.assertTrue(r["all_leads_not_verified"])

class TestPhase197Classifier(unittest.TestCase):
    def test_classifier(self):
        r = build_source_category_classifier()["phase197_source_category_classifier"]
        self.assertEqual(r["category_count"], 6)

class TestPhase197Reliability(unittest.TestCase):
    def test_reliability(self):
        r = build_source_reliability_pre_score()["phase197_source_reliability_pre_score"]
        self.assertEqual(r["score_count"], 6)

class TestPhase197Dedup(unittest.TestCase):
    def test_dedup(self):
        r = build_dedup(True)["phase197_dedup"]
        self.assertGreater(r["items_checked"], 0)

class TestPhase197Converter(unittest.TestCase):
    def test_converter(self):
        r = build_dirty_inbox_converter(True)["phase197_converted_items"]
        self.assertGreater(r["converted_count"], 0)
        self.assertTrue(r["all_converted_not_clean_evidence"])

class TestPhase197IngestionManifest(unittest.TestCase):
    def test_manifest(self):
        r = build_ingestion_manifest(True)["phase197_ingestion_manifest"]
        self.assertTrue(r["manifest_generated"])
        self.assertGreater(r["ingested"], 0)

class TestPhase197Alignment(unittest.TestCase):
    def test_alignment(self):
        r = build_same_market_alignment_preview(True)["phase197_same_market_alignment_preview"]
        self.assertGreater(r["alignment_count"], 0)
        self.assertTrue(r["same_market"])
        self.assertTrue(r["all_alignments_preview"])

class TestPhase197RerunReadiness(unittest.TestCase):
    def test_rerun(self):
        r = build_phase196_rerun_readiness(True)["phase197_phase196_rerun_readiness"]
        self.assertTrue(r["rerun_recommended"])

class TestPhase197NextTasks(unittest.TestCase):
    def test_tasks(self):
        r = build_next_verification_task_seed(True)["phase197_next_verification_task_seed"]
        self.assertGreaterEqual(r["task_count"], 0)
        self.assertTrue(r["all_tasks_seed_only"])

class TestPhase197BlockedHandler(unittest.TestCase):
    def test_blocked(self):
        r = build_blocked_source_handler(True)["phase197_blocked_source_handler"]
        self.assertTrue(r["300394_cninfo_retained"])

class TestPhase197ScoutBoard(unittest.TestCase):
    def test_board(self):
        r = build_scout_board(True)["phase197_scout_board"]
        self.assertTrue(r["board_generated"])
        self.assertTrue(r["300394_cninfo_blocker_retained"])

class TestPhase197ScoutBrief(unittest.TestCase):
    def test_brief(self):
        r = build_scout_brief(True)["phase197_scout_brief"]
        self.assertTrue(r["brief_generated"])
        self.assertIn("boss_summary", r)

class TestPhase197Backlog(unittest.TestCase):
    def test_backlog(self):
        r = build_backlog_update(True)["phase197_backlog_update"]
        self.assertTrue(r["backlog_generated"])

class TestPhase197Guard(unittest.TestCase):
    def test_guard_pass(self):
        r = build_cannot_conclude_guard(True)["phase197_cannot_conclude_guard"]
        self.assertTrue(r["guard_pass"])
        self.assertEqual(r["violations_count"], 0)

class TestPhase197QualityGate(unittest.TestCase):
    def test_gate(self):
        r = build_quality_gate(True)["phase197_quality_gate"]
        self.assertTrue(r["gate_pass"])

class TestPhase197Dashboard(unittest.TestCase):
    def test_dashboard(self):
        r = build_dashboard(True)["phase197_dashboard"]
        self.assertTrue(r["dashboard_generated"])
        self.assertGreater(r["summary"]["leads_total"], 0)
    def test_safety(self):
        r = build_dashboard(True)["phase197_dashboard"]
        s = r["safety"]
        self.assertFalse(s["mock_used"])
        self.assertFalse(s["clean_evidence_created"])
        self.assertFalse(s["trade_recommendation_created"])
        self.assertFalse(s["classifier_executed"])
        self.assertFalse(s["real_verification_executed"])

if __name__ == '__main__':
    unittest.main()
