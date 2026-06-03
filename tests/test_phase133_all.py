import unittest,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

from smr_phase133_config import load_config
from smr_phase133_domain_registry import build_domain_registry
from smr_phase133_phase132_coverage_loader import load_phase132_coverage
from smr_phase133_seasonal_period_registry import build_seasonal_period_registry
from smr_phase133_ticker_financial_valuation_loader import build_ticker_financial_valuation_loader
from smr_phase133_ticker_seasonal_profile_builder import build_ticker_seasonal_profiles
from smr_phase133_cross_market_comparison_builder import build_cross_market_comparison
from smr_phase133_financial_trend_panel_builder import build_financial_trend_panel
from smr_phase133_valuation_trend_panel_builder import build_valuation_trend_panel
from smr_phase133_opportunity_catalyst_panel_builder import build_opportunity_catalyst_panel
from smr_phase133_watchlist_status_panel_builder import build_watchlist_status_panel
from smr_phase133_source_coverage_panel_builder import build_source_coverage_panel
from smr_phase133_signal_effectiveness_panel_builder import build_signal_effectiveness_panel
from smr_phase133_gap_risk_panel_builder import build_gap_risk_panel
from smr_phase133_owner_action_queue_builder import build_owner_action_queue
from smr_phase133_seasonal_analytics_board import build_seasonal_analytics_board
from smr_phase133_seasonal_analytics_brief import build_seasonal_analytics_brief_md
from smr_phase133_seasonal_dashboard_exporter import build_seasonal_dashboard_export
from smr_phase133_seasonal_memory import build_seasonal_memory
from smr_phase133_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase133_backlog_update import build_backlog_update

class TestPhase133Config(unittest.TestCase):
    def test_loads(self): self.assertEqual(load_config()["phase"],"phase133")
    def test_research_only(self): self.assertTrue(load_config()["research_only"])
    def test_seasonal_panels(self): self.assertEqual(len(load_config()["seasonal_panels"]),9)

class TestPhase133DomainRegistry(unittest.TestCase):
    def test_has_domains(self): self.assertGreater(build_domain_registry()["phase133_domain_registry"]["total"],15)

class TestPhase133Phase132CoverageLoader(unittest.TestCase):
    def test_all_8(self): self.assertTrue(load_phase132_coverage()["phase133_phase132_coverage_loader"]["all_8_full_coverage"])

class TestPhase133SeasonalPeriodRegistry(unittest.TestCase):
    def test_periods(self): self.assertEqual(build_seasonal_period_registry()["phase133_seasonal_period_registry"]["total_periods"],7)

class TestPhase133TickerFinancialValuationLoader(unittest.TestCase):
    def test_count(self): self.assertEqual(build_ticker_financial_valuation_loader()["phase133_ticker_financial_valuation_loader"]["total"],8)
    def test_all_sources(self): r=build_ticker_financial_valuation_loader()["phase133_ticker_financial_valuation_loader"];self.assertTrue(r["all_have_financial_source"]);self.assertTrue(r["all_have_valuation_source"])

class TestPhase133TickerSeasonalProfileBuilder(unittest.TestCase):
    def test_count(self): self.assertEqual(build_ticker_seasonal_profiles()["phase133_ticker_seasonal_profile_builder"]["total"],8)

class TestPhase133CrossMarketComparisonBuilder(unittest.TestCase):
    def test_not_advice(self): self.assertTrue(build_cross_market_comparison()["phase133_cross_market_comparison_builder"]["not_investment_advice"])

class TestPhase133FinancialTrendPanelBuilder(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_financial_trend_panel()["phase133_financial_trend_panel_builder"]["ready_for_data_population"])

class TestPhase133ValuationTrendPanelBuilder(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_valuation_trend_panel()["phase133_valuation_trend_panel_builder"]["ready_for_data_population"])

class TestPhase133OpportunityCatalystPanelBuilder(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_opportunity_catalyst_panel()["phase133_opportunity_catalyst_panel_builder"]["ready_for_seasonal_tracking"])

class TestPhase133WatchlistStatusPanelBuilder(unittest.TestCase):
    def test_not_advice(self): self.assertTrue(build_watchlist_status_panel()["phase133_watchlist_status_panel_builder"]["not_investment_advice"])

class TestPhase133SourceCoveragePanelBuilder(unittest.TestCase):
    def test_all_critical(self): self.assertTrue(build_source_coverage_panel()["phase133_source_coverage_panel_builder"]["all_critical_sources_available"])

class TestPhase133SignalEffectivenessPanelBuilder(unittest.TestCase):
    def test_first_snapshot(self): self.assertTrue(build_signal_effectiveness_panel()["phase133_signal_effectiveness_panel_builder"]["first_seasonal_snapshot"])

class TestPhase133GapRiskPanelBuilder(unittest.TestCase):
    def test_no_critical(self): self.assertTrue(build_gap_risk_panel()["phase133_gap_risk_panel_builder"]["no_critical_gaps"])

class TestPhase133OwnerActionQueueBuilder(unittest.TestCase):
    def test_no_trade(self): self.assertTrue(build_owner_action_queue()["phase133_owner_action_queue_builder"]["no_trade_actions"])

class TestPhase133SeasonalAnalyticsBoard(unittest.TestCase):
    def test_not_trade(self): self.assertTrue(build_seasonal_analytics_board()["phase133_seasonal_analytics_board"]["not_trade_board"])

class TestPhase133SeasonalAnalyticsBrief(unittest.TestCase):
    def test_has_content(self): self.assertIn("Portfolio Overview",build_seasonal_analytics_brief_md())

class TestPhase133SeasonalDashboardExporter(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_seasonal_dashboard_export()["phase133_seasonal_dashboard_exporter"]["export_ready"])

class TestPhase133SeasonalMemory(unittest.TestCase):
    def test_gitignored(self): self.assertTrue(build_seasonal_memory()["phase133_seasonal_memory"]["gitignored"])

class TestPhase133CannotConcludeGuard(unittest.TestCase):
    def test_pass(self):
        r=run_cannot_conclude_guard()
        self.assertEqual(r["phase133_cannot_conclude_guard"]["overall"],"pass")
        self.assertEqual(r["phase133_cannot_conclude_guard"]["violations"],0)

class TestPhase133BacklogUpdate(unittest.TestCase):
    def test_next_phase(self): self.assertIn("phase134",build_backlog_update()["phase133_backlog_update"]["next_phase"])

class TestPhase133RegressionGate(unittest.TestCase):
    def test_phase132_regression(self):
        from smr_phase132_cannot_conclude_guard import run_cannot_conclude_guard as g132
        self.assertEqual(g132()["phase132_cannot_conclude_guard"]["overall"],"pass")
    def test_phase131_regression(self):
        from smr_phase131_cannot_conclude_guard import run_cannot_conclude_guard as g131
        self.assertEqual(g131()["phase131_cannot_conclude_guard"]["overall"],"pass")

if __name__=="__main__":
    unittest.main()