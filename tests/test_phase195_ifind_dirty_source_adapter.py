# Tests for Phase195 iFinD Dirty Source Adapter
import json, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '08_scripts', 'lib'))
from smr_phase195_ifind_dirty_source_adapter import (
    build_phase195_config, build_domain_registry, build_cn_a_dirty_source_universe,
    build_news_query_plan, build_announcement_query_plan, build_event_query_plan,
    build_wencai_query_plan, build_source_metadata_schema, build_source_lead_observation_schema,
    build_copyright_policy, build_source_category_classifier, build_source_reliability_pre_score,
    build_ingestion_preview, build_metadata_validation, build_copyright_validator,
    build_dedup_manifest, build_cross_check_route_preview, build_web_scout_bridge_preview,
    build_ingestion_manifest, build_dirty_source_board, build_dirty_source_brief,
    build_backlog_update, build_cannot_conclude_guard, build_quality_gate, build_dashboard,
    CN_A_TICKERS, DIRTY_LANES, MAX_EXCERPT_WORDS
)

class TestPhase195Config(unittest.TestCase):
    def test_config_loaded(self):
        r = build_phase195_config()['phase195_config']
        self.assertTrue(r['config_loaded'])
        self.assertEqual(r['phase'], 'phase195')
        self.assertEqual(r['cn_a_ticker_count'], 4)
    def test_strategy_correct(self):
        r = build_phase195_config()['phase195_config']
        self.assertIn('dirty_source', r['strategy'])
    def test_safety_flags(self):
        r = build_phase195_config()['phase195_config']
        self.assertTrue(r['clean_evidence_disabled'])
        self.assertTrue(r['trade_disabled'])
        self.assertFalse(r['mock_used'])
        self.assertFalse(r['fixture_used'])

class TestPhase195DomainRegistry(unittest.TestCase):
    def test_registry_defined(self):
        r = build_domain_registry()['phase195_domain_registry']
        self.assertTrue(r['registry_defined'])
        self.assertGreater(r['domain_count'], 0)
    def test_all_via_ifind(self):
        r = build_domain_registry()['phase195_domain_registry']
        self.assertTrue(r['all_via_ifind'])

class TestPhase195Universe(unittest.TestCase):
    def test_ticker_count(self):
        r = build_cn_a_dirty_source_universe()['phase195_cn_a_dirty_source_universe']
        self.assertEqual(r['tickers_total'], 4)
        self.assertEqual(r['dirty_source_enabled'], 4)
    def test_300394_blocked(self):
        r = build_cn_a_dirty_source_universe()['phase195_cn_a_dirty_source_universe']
        blocked = [row for row in r['rows'] if row['blocked']]
        self.assertEqual(len(blocked), 1)
        self.assertEqual(blocked[0]['ticker'], '300394.SZ')
        self.assertIn('cninfo', blocked[0]['blocker'])
    def test_hk_us_not_in_scope(self):
        r = build_cn_a_dirty_source_universe()['phase195_cn_a_dirty_source_universe']
        self.assertTrue(r['hk_us_not_in_scope'])

class TestPhase195QueryPlans(unittest.TestCase):
    def test_news_plan(self):
        r = build_news_query_plan(False)['phase195_news_query_plan']
        self.assertTrue(r['plan_defined'])
        self.assertGreater(r['queries_designed'], 0)
    def test_announcement_plan(self):
        r = build_announcement_query_plan(False)['phase195_announcement_query_plan']
        self.assertTrue(r['plan_defined'])
    def test_event_plan(self):
        r = build_event_query_plan(False)['phase195_event_query_plan']
        self.assertTrue(r['plan_defined'])
    def test_wencai_plan(self):
        r = build_wencai_query_plan(False)['phase195_wencai_query_plan']
        self.assertTrue(r['plan_defined'])
    def test_dry_run_no_network(self):
        r = build_news_query_plan(False)['phase195_news_query_plan']
        self.assertTrue(r['dry_run'])
        self.assertFalse(r['network_called'])
    def test_allow_network(self):
        r = build_news_query_plan(True)['phase195_news_query_plan']
        self.assertTrue(r['network_called'])

class TestPhase195MetadataSchema(unittest.TestCase):
    def test_schema_defined(self):
        r = build_source_metadata_schema()['phase195_source_metadata_schema']
        self.assertIn('source_id', r['required_fields'])
        self.assertTrue(r['raw_disallowed'])

class TestPhase195ObservationSchema(unittest.TestCase):
    def test_schema_defined(self):
        r = build_source_lead_observation_schema()['phase195_source_lead_observation_schema']
        self.assertIn('observation_id', r['observation_fields'])
        self.assertTrue(r['not_clean_evidence'])

class TestPhase195CopyrightPolicy(unittest.TestCase):
    def test_policy(self):
        r = build_copyright_policy()['phase195_copyright_policy']
        self.assertEqual(r['max_excerpt_words'], 25)
        self.assertTrue(r['full_text_disallowed'])

class TestPhase195CategoryClassifier(unittest.TestCase):
    def test_classifier(self):
        r = build_source_category_classifier()['phase195_source_category_classifier']
        self.assertEqual(r['category_count'], 4)
        self.assertTrue(r['all_via_ifind'])

class TestPhase195ReliabilityPreScore(unittest.TestCase):
    def test_scores(self):
        r = build_source_reliability_pre_score()['phase195_source_reliability_pre_score']
        self.assertEqual(r['score_count'], 4)
        self.assertTrue(r['all_pre_scores_tentative'])

class TestPhase195IngestionPreview(unittest.TestCase):
    def test_preview_dry(self):
        r = build_ingestion_preview(False)['phase195_ingestion_preview']
        self.assertGreater(r['dirty_item_count'], 0)
    def test_preview_execute(self):
        r = build_ingestion_preview(True)['phase195_ingestion_preview']
        self.assertGreater(r['dirty_item_count'], 0)
    def test_items_not_clean_evidence(self):
        r = build_ingestion_preview(True)['phase195_ingestion_preview']
        self.assertTrue(r['all_items_not_clean_evidence'])
    def test_excerpts_within_limit(self):
        r = build_ingestion_preview(True)['phase195_ingestion_preview']
        self.assertTrue(r['all_excerpts_within_limit'])
    def test_no_raw_saved(self):
        r = build_ingestion_preview(True)['phase195_ingestion_preview']
        self.assertTrue(r['all_raw_full_text_false'])
    def test_lane_breakdown(self):
        r = build_ingestion_preview(True)['phase195_ingestion_preview']
        for lane in DIRTY_LANES:
            self.assertIn(lane, r['lane_breakdown'])

class TestPhase195MetadataValidation(unittest.TestCase):
    def test_validation(self):
        r = build_metadata_validation(True)['phase195_metadata_validation']
        self.assertGreater(r['items_checked'], 0)
        self.assertEqual(r['invalid_count'], 0)

class TestPhase195CopyrightValidator(unittest.TestCase):
    def test_all_safe(self):
        r = build_copyright_validator(True)['phase195_copyright_validation']
        self.assertTrue(r['all_copyright_safe'])

class TestPhase195Dedup(unittest.TestCase):
    def test_dedup(self):
        r = build_dedup_manifest(True)['phase195_dedup_manifest']
        self.assertGreater(r['items_checked'], 0)

class TestPhase195CrossCheckRoute(unittest.TestCase):
    def test_routes(self):
        r = build_cross_check_route_preview(True)['phase195_cross_check_route_preview']
        self.assertGreater(r['route_count'], 0)
        self.assertTrue(r['all_routes_preview_only'])

class TestPhase195WebScoutBridge(unittest.TestCase):
    def test_bridges(self):
        r = build_web_scout_bridge_preview(True)['phase195_web_scout_bridge_preview']
        self.assertGreater(r['bridge_count'], 0)
        self.assertTrue(r['all_bridges_preview_only'])

class TestPhase195IngestionManifest(unittest.TestCase):
    def test_manifest(self):
        r = build_ingestion_manifest(True)['phase195_ingestion_manifest']
        self.assertTrue(r['manifest_generated'])
        self.assertGreater(r['ingested'], 0)

class TestPhase195DirtySourceBoard(unittest.TestCase):
    def test_board(self):
        r = build_dirty_source_board(True)['phase195_dirty_source_board']
        self.assertTrue(r['board_generated'])
        for s in ['strengthened', 'weakened', 'unchanged', 'anomaly', 'blocked']:
            self.assertIn(s, r['sections'])
    def test_300394_blocker_retained(self):
        r = build_dirty_source_board(True)['phase195_dirty_source_board']
        self.assertTrue(r['300394_blocker_retained'])
    def test_board_not_trade_signal(self):
        r = build_dirty_source_board(True)['phase195_dirty_source_board']
        self.assertTrue(r['board_not_trade_signal'])

class TestPhase195DirtySourceBrief(unittest.TestCase):
    def test_brief(self):
        r = build_dirty_source_brief(True)['phase195_dirty_source_brief']
        self.assertTrue(r['brief_generated'])
        self.assertIn('boss_summary', r)
    def test_no_trade_advice(self):
        r = build_dirty_source_brief(True)['phase195_dirty_source_brief']
        self.assertTrue(r['brief_not_trade_advice'])

class TestPhase195BacklogUpdate(unittest.TestCase):
    def test_backlog(self):
        r = build_backlog_update(True)['phase195_backlog_update']
        self.assertTrue(r['backlog_generated'])

class TestPhase195CannotConcludeGuard(unittest.TestCase):
    def test_guard_pass(self):
        r = build_cannot_conclude_guard(True)['phase195_cannot_conclude_guard']
        self.assertTrue(r['guard_pass'])
        self.assertEqual(r['violations_count'], 0)
    def test_guard_not_clean_evidence(self):
        r = build_cannot_conclude_guard(True)['phase195_cannot_conclude_guard']
        self.assertTrue(r['guard_not_clean_evidence'])

class TestPhase195QualityGate(unittest.TestCase):
    def test_gate_pass(self):
        r = build_quality_gate(True)['phase195_quality_gate']
        self.assertTrue(r['gate_pass'])
    def test_gate_not_trade_signal(self):
        r = build_quality_gate(True)['phase195_quality_gate']
        self.assertTrue(r['gate_not_trade_signal'])

class TestPhase195Dashboard(unittest.TestCase):
    def test_dashboard(self):
        r = build_dashboard(True)['phase195_dashboard']
        self.assertTrue(r['dashboard_generated'])
        self.assertEqual(r['summary']['tickers_total'], 4)
    def test_safety(self):
        r = build_dashboard(True)['phase195_dashboard']
        s = r['safety']
        self.assertFalse(s['mock_used'])
        self.assertFalse(s['fixture_used'])
        self.assertFalse(s['raw_full_text_saved'])
        self.assertFalse(s['clean_evidence_created'])
        self.assertFalse(s['packet_updated'])
        self.assertFalse(s['watch_core_updated'])
        self.assertFalse(s['trade_recommendation_created'])
        self.assertFalse(s['target_price_created'])
        self.assertFalse(s['position_sizing_created'])
        self.assertFalse(s['broker_api_called'])
        self.assertFalse(s['llm_api_called'])

if __name__ == '__main__':
    unittest.main()
