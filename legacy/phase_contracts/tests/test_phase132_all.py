import unittest,json,sys,os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "08_scripts" / "lib"))

from smr_phase132_config import load_config
from smr_phase132_domain_registry import build_domain_registry
from smr_phase132_phase131_coverage_loader import load_phase131_coverage
from smr_phase132_historical_valuation_gap_loader import load_historical_valuation_gap
from smr_phase132_valuation_source_registry import build_valuation_source_registry
from smr_phase132_eastmoney_valuation_adapter import build_eastmoney_valuation_adapter
from smr_phase132_akshare_star_valuation_adapter import build_akshare_star_valuation_adapter
from smr_phase132_third_party_valuation_fallback import build_third_party_valuation_fallback
from smr_phase132_financial_metric_dependency_resolver import build_financial_metric_dependency_resolver
from smr_phase132_ev_ebitda_input_builder import build_ev_ebitda_input
from smr_phase132_ps_ratio_input_builder import build_ps_ratio_input
from smr_phase132_alternative_valuation_metric_builder import build_alternative_valuation_metrics
from smr_phase132_valuation_source_normalizer import build_valuation_source_normalizer
from smr_phase132_valuation_quality_gate import build_valuation_quality_gate
from smr_phase132_valuation_coverage_classifier import classify_valuation_coverage
from smr_phase132_hard_data_valuation_update import build_hard_data_valuation_update
from smr_phase132_watchlist_valuation_update import build_watchlist_valuation_update
from smr_phase132_daily_brief_valuation_update import build_daily_brief_valuation_update
from smr_phase132_signal_effectiveness_valuation_update import build_signal_effectiveness_valuation_update
from smr_phase132_gap_closeout_report import build_gap_closeout_report
from smr_phase132_valuation_integration_board import build_valuation_integration_board
from smr_phase132_valuation_integration_brief import build_valuation_integration_brief_md
from smr_phase132_valuation_memory import build_valuation_memory
from smr_phase132_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase132_backlog_update import build_backlog_update

class TestPhase132Config(unittest.TestCase):
    def test_loads(self): self.assertEqual(load_config()["phase"],"phase132")
    def test_target(self): self.assertEqual(load_config()["target_ticker"],"688041.SH")
    def test_research_only(self): self.assertTrue(load_config()["research_only"])

class TestPhase132DomainRegistry(unittest.TestCase):
    def test_has_domains(self): self.assertGreater(build_domain_registry()["phase132_domain_registry"]["total"],15)

class TestPhase132Phase131CoverageLoader(unittest.TestCase):
    def test_688041_partial(self): self.assertEqual(load_phase131_coverage()["phase132_phase131_coverage_loader"]["688041_status"],"partial_valuation_incomplete")

class TestPhase132HistoricalValuationGapLoader(unittest.TestCase):
    def test_first_attempt(self): self.assertTrue(load_historical_valuation_gap()["phase132_historical_valuation_gap_loader"]["this_is_the_first_valuation_hardening_attempt"])

class TestPhase132ValuationSourceRegistry(unittest.TestCase):
    def test_all_available(self): self.assertTrue(build_valuation_source_registry()["phase132_valuation_source_registry"]["all_available"])

class TestPhase132EastmoneyValuationAdapter(unittest.TestCase):
    def test_feasible(self): self.assertTrue(build_eastmoney_valuation_adapter()["phase132_eastmoney_valuation_adapter"]["valuation_feasible"])

class TestPhase132AkshareStarValuationAdapter(unittest.TestCase):
    def test_feasible(self): self.assertTrue(build_akshare_star_valuation_adapter()["phase132_akshare_star_valuation_adapter"]["valuation_feasible"])

class TestPhase132ThirdPartyValuationFallback(unittest.TestCase):
    def test_has_fallbacks(self): self.assertGreater(build_third_party_valuation_fallback()["phase132_third_party_valuation_fallback"]["total"],0)

class TestPhase132FinancialMetricDependencyResolver(unittest.TestCase):
    def test_all_derivable(self): self.assertTrue(build_financial_metric_dependency_resolver()["phase132_financial_metric_dependency_resolver"]["all_key_metrics_derivable"])

class TestPhase132EvEbitdaInputBuilder(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_ev_ebitda_input()["phase132_ev_ebitda_input_builder"]["calculation_ready"])

class TestPhase132PsRatioInputBuilder(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_ps_ratio_input()["phase132_ps_ratio_input_builder"]["calculation_ready"])

class TestPhase132AlternativeValuationMetricBuilder(unittest.TestCase):
    def test_core_covered(self): self.assertTrue(build_alternative_valuation_metrics()["phase132_alternative_valuation_metric_builder"]["core_valuation_covered"])

class TestPhase132ValuationSourceNormalizer(unittest.TestCase):
    def test_all_normalized(self): self.assertTrue(build_valuation_source_normalizer()["phase132_valuation_source_normalizer"]["all_core_metrics_normalized"])

class TestPhase132ValuationQualityGate(unittest.TestCase):
    def test_pass(self):
        r=build_valuation_quality_gate()
        self.assertEqual(r["phase132_valuation_quality_gate"]["overall"],"pass")

class TestPhase132ValuationCoverageClassifier(unittest.TestCase):
    def test_feasible(self): self.assertTrue(classify_valuation_coverage()["phase132_valuation_coverage_classifier"]["688041_valuation_feasible"])

class TestPhase132HardDataValuationUpdate(unittest.TestCase):
    def test_full_coverage(self): self.assertTrue(build_hard_data_valuation_update()["phase132_hard_data_valuation_update"]["all_8_tickers_full_coverage"])

class TestPhase132WatchlistValuationUpdate(unittest.TestCase):
    def test_resolved(self): self.assertTrue(build_watchlist_valuation_update()["phase132_watchlist_valuation_update"]["688041_partial_resolved"])
    def test_no_trade(self): r=build_watchlist_valuation_update();self.assertEqual(r["phase132_watchlist_valuation_update"]["pending_created"],0)

class TestPhase132DailyBriefValuationUpdate(unittest.TestCase):
    def test_added(self): self.assertTrue(build_daily_brief_valuation_update()["phase132_daily_brief_valuation_update"]["688041_valuation_added_to_brief"])

class TestPhase132SignalEffectivenessValuationUpdate(unittest.TestCase):
    def test_added(self): self.assertTrue(build_signal_effectiveness_valuation_update()["phase132_signal_effectiveness_valuation_update"]["688041_valuation_added_to_signals"])

class TestPhase132GapCloseoutReport(unittest.TestCase):
    def test_closed(self): self.assertTrue(build_gap_closeout_report()["phase132_gap_closeout_report"]["all_8_tickers_now_full_coverage"])

class TestPhase132ValuationIntegrationBoard(unittest.TestCase):
    def test_not_trade(self): self.assertTrue(build_valuation_integration_board()["phase132_valuation_integration_board"]["not_trade_board"])

class TestPhase132ValuationIntegrationBrief(unittest.TestCase):
    def test_has_content(self): self.assertIn("688041",build_valuation_integration_brief_md())

class TestPhase132ValuationMemory(unittest.TestCase):
    def test_gitignored(self): self.assertTrue(build_valuation_memory()["phase132_valuation_memory"]["gitignored"])

class TestPhase132CannotConcludeGuard(unittest.TestCase):
    def test_pass(self):
        r=run_cannot_conclude_guard()
        self.assertEqual(r["phase132_cannot_conclude_guard"]["overall"],"pass")
        self.assertEqual(r["phase132_cannot_conclude_guard"]["violations"],0)

class TestPhase132BacklogUpdate(unittest.TestCase):
    def test_all_resolved(self): self.assertTrue(build_backlog_update()["phase132_backlog_update"]["all_gaps_resolved"])
    def test_next_phase(self): self.assertIn("phase133",build_backlog_update()["phase132_backlog_update"]["next_phase"])

class TestPhase132RegressionGate(unittest.TestCase):
    def test_phase131_regression(self):
        from smr_phase131_cannot_conclude_guard import run_cannot_conclude_guard as g131
        self.assertEqual(g131()["phase131_cannot_conclude_guard"]["overall"],"pass")
    def test_phase130_regression(self):
        from smr_phase130_cannot_conclude_guard import run_cannot_conclude_guard as g130
        self.assertEqual(g130()["phase130_cannot_conclude_guard"]["overall"],"pass")

if __name__=="__main__":
    unittest.main()
