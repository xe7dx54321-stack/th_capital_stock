import unittest,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

from smr_phase134_config import load_config
from smr_phase134_domain_registry import build_domain_registry
from smr_phase134_phase133_dashboard_loader import load_phase133_dashboard
from smr_phase134_console_data_aggregator import build_console_data_aggregator
from smr_phase134_ticker_card_builder import build_ticker_cards
from smr_phase134_market_section_builder import build_market_sections
from smr_phase134_research_priority_builder import build_research_priority
from smr_phase134_seasonal_insight_center import build_seasonal_insight_center
from smr_phase134_watchlist_status_center import build_watchlist_status_center
from smr_phase134_opportunity_catalyst_center import build_opportunity_catalyst_center
from smr_phase134_source_signal_quality_center import build_source_signal_quality_center
from smr_phase134_gap_risk_center import build_gap_risk_center
from smr_phase134_owner_action_center import build_owner_action_center
from smr_phase134_daily_brief_preview import build_daily_brief_preview
from smr_phase134_memory_feedback_center import build_memory_feedback_center
from smr_phase134_system_health_snapshot import build_system_health_snapshot
from smr_phase134_artifact_link_index import build_artifact_link_index
from smr_phase134_console_quality_gate import run_console_quality_gate
from smr_phase134_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase134_backlog_update import build_backlog_update
from smr_phase134_console_memory import build_console_memory

class TestPhase134Config(unittest.TestCase):
    def test_loads(self): self.assertEqual(load_config()["phase"],"phase134")
    def test_research_only(self): self.assertTrue(load_config()["research_only"])
    def test_console_enabled(self): self.assertTrue(load_config()["personal_research_console_enabled"])
    def test_panels_count(self): self.assertGreaterEqual(len(load_config()["console_panels"]),10)
    def test_tickers_8(self): self.assertEqual(len(load_config()["universe_tickers"]),8)
    def test_safety_all_disabled(self):
        s=load_config()["safety"]
        self.assertFalse(s["mock"]);self.assertFalse(s["fixture"]);self.assertFalse(s["raw"])
        self.assertFalse(s["trade_recommendation_allowed"]);self.assertFalse(s["target_price_output_allowed"])

class TestPhase134DomainRegistry(unittest.TestCase):
    def test_has_domains(self): self.assertGreater(build_domain_registry()["phase134_domain_registry"]["total"],15)
    def test_all_research_only(self): self.assertTrue(build_domain_registry()["phase134_domain_registry"]["all_research_only"])

class TestPhase134Phase133DashboardLoader(unittest.TestCase):
    def test_loaded(self): self.assertTrue(load_phase133_dashboard()["phase134_phase133_dashboard_loader"]["status"]["phase133_loaded"])
    def test_all_8(self): self.assertTrue(load_phase133_dashboard()["phase134_phase133_dashboard_loader"]["status"]["all_8_full_coverage"])

class TestPhase134ConsoleDataAggregator(unittest.TestCase):
    def test_total_8(self): self.assertEqual(build_console_data_aggregator()["phase134_console_data_aggregator"]["data"]["tickers_total"],8)
    def test_all_covered(self): self.assertTrue(build_console_data_aggregator()["phase134_console_data_aggregator"]["data"]["all_8_full_coverage"])

class TestPhase134TickerCardBuilder(unittest.TestCase):
    def test_8_cards(self): self.assertEqual(build_ticker_cards()["phase134_ticker_card_builder"]["ticker_cards_created"],8)
    def test_not_trade(self): self.assertTrue(build_ticker_cards()["phase134_ticker_card_builder"]["not_trade_signal"])
    def test_300394_blocker(self):
        cards=build_ticker_cards()["phase134_ticker_card_builder"]["cards"]
        c394=[c for c in cards if c["ticker"]=="300394.SZ"][0]
        self.assertEqual(c394["blocker"],"cninfo_org_id_missing")
        self.assertTrue(c394["financial_covered"])

class TestPhase134MarketSectionBuilder(unittest.TestCase):
    def test_3_sections(self): self.assertEqual(build_market_sections()["phase134_market_section_builder"]["market_sections_created"],3)
    def test_currency_boundary(self): self.assertIn("not_directly_compared",build_market_sections()["phase134_market_section_builder"]["currency_boundary"])

class TestPhase134ResearchPriorityBuilder(unittest.TestCase):
    def test_8_priorities(self): self.assertEqual(build_research_priority()["phase134_research_priority_builder"]["total"],8)
    def test_not_trade(self): self.assertTrue(build_research_priority()["phase134_research_priority_builder"]["not_trade_signal"])

class TestPhase134SeasonalInsightCenter(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_seasonal_insight_center()["phase134_seasonal_insight_center"]["ready_for_owner_review"])

class TestPhase134WatchlistStatusCenter(unittest.TestCase):
    def test_8_statuses(self): self.assertEqual(build_watchlist_status_center()["phase134_watchlist_status_center"]["total"],8)
    def test_not_trade(self): self.assertTrue(build_watchlist_status_center()["phase134_watchlist_status_center"]["not_trade_signal"])

class TestPhase134OpportunityCatalystCenter(unittest.TestCase):
    def test_catalysts(self): self.assertGreater(build_opportunity_catalyst_center()["phase134_opportunity_catalyst_center"]["total"],3)
    def test_not_trade(self): self.assertTrue(build_opportunity_catalyst_center()["phase134_opportunity_catalyst_center"]["not_trade_signal"])

class TestPhase134SourceSignalQualityCenter(unittest.TestCase):
    def test_all_critical(self): self.assertTrue(build_source_signal_quality_center()["phase134_source_signal_quality_center"]["all_critical_sources_available"])
    def test_not_trade(self): self.assertTrue(build_source_signal_quality_center()["phase134_source_signal_quality_center"]["not_trade_signal"])

class TestPhase134GapRiskCenter(unittest.TestCase):
    def test_no_critical(self): self.assertTrue(build_gap_risk_center()["phase134_gap_risk_center"]["no_critical_gaps"])
    def test_not_trade(self): self.assertTrue(build_gap_risk_center()["phase134_gap_risk_center"]["not_trade_signal"])

class TestPhase134OwnerActionCenter(unittest.TestCase):
    def test_actions_created(self): self.assertGreater(build_owner_action_center()["phase134_owner_action_center"]["owner_actions_created"],3)
    def test_no_trade_actions(self): self.assertEqual(build_owner_action_center()["phase134_owner_action_center"]["trade_actions"],0)
    def test_not_trade(self): self.assertTrue(build_owner_action_center()["phase134_owner_action_center"]["not_trade_signal"])

class TestPhase134DailyBriefPreview(unittest.TestCase):
    def test_active(self): self.assertTrue(build_daily_brief_preview()["phase134_daily_brief_preview"]["preview"]["daily_brief_active"])
    def test_not_trade(self): self.assertTrue(build_daily_brief_preview()["phase134_daily_brief_preview"]["not_trade_signal"])

class TestPhase134MemoryFeedbackCenter(unittest.TestCase):
    def test_active(self): self.assertTrue(build_memory_feedback_center()["phase134_memory_feedback_center"]["records"]["evidence_memory_active"])
    def test_path_ignored(self): self.assertTrue(build_memory_feedback_center()["phase134_memory_feedback_center"]["records"]["memory_path_ignored"])

class TestPhase134SystemHealthSnapshot(unittest.TestCase):
    def test_healthy(self): self.assertEqual(build_system_health_snapshot()["phase134_system_health_snapshot"]["health"]["system_status"],"healthy")
    def test_no_trade(self): self.assertEqual(build_system_health_snapshot()["phase134_system_health_snapshot"]["health"]["trade_checks"]["pending"],0)

class TestPhase134ArtifactLinkIndex(unittest.TestCase):
    def test_links(self): self.assertGreater(build_artifact_link_index()["phase134_artifact_link_index"]["total"],5)

class TestPhase134ConsoleQualityGate(unittest.TestCase):
    def test_pass(self): self.assertEqual(run_console_quality_gate()["phase134_console_quality_gate"]["overall"],"pass")
    def test_violations_0(self): self.assertEqual(run_console_quality_gate()["phase134_console_quality_gate"]["violations"],0)
    def test_research_only(self): self.assertEqual(run_console_quality_gate()["phase134_console_quality_gate"]["mode"],"personal_research_console")

class TestPhase134CannotConcludeGuard(unittest.TestCase):
    def test_pass(self): self.assertEqual(run_cannot_conclude_guard()["phase134_cannot_conclude_guard"]["overall"],"pass")
    def test_violations_0(self): self.assertEqual(run_cannot_conclude_guard()["phase134_cannot_conclude_guard"]["violations"],0)
    def test_research_only(self): self.assertIn("research_only",run_cannot_conclude_guard()["phase134_cannot_conclude_guard"]["mode"])

class TestPhase134BacklogUpdate(unittest.TestCase):
    def test_console_deployed(self): self.assertIn("console",build_backlog_update()["phase134_backlog_update"]["phase134_status"])
    def test_next_phase(self): self.assertIn("phase135",build_backlog_update()["phase134_backlog_update"]["next_phase"])

class TestPhase134ConsoleMemory(unittest.TestCase):
    def test_records(self): self.assertGreater(build_console_memory()["phase134_console_memory"]["records_written"],2)
    def test_path_ignored(self): self.assertTrue(build_console_memory()["phase134_console_memory"]["memory_path_ignored"])

class TestPhase134RegressionGate(unittest.TestCase):
    def test_phase133_regression(self):
        r=load_phase133_dashboard()["phase134_phase133_dashboard_loader"]["status"]
        self.assertTrue(r["phase133_loaded"])
        self.assertTrue(r["all_8_full_coverage"])
        self.assertTrue(r["phase133_guard_pass"])

if __name__=="__main__":
    unittest.main()
