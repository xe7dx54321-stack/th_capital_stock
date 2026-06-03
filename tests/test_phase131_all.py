import unittest,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

from smr_phase131_config import load_config
from smr_phase131_domain_registry import build_domain_registry
from smr_phase131_phase130_resolution_loader import load_phase130_resolution
from smr_phase131_alternative_source_registry_loader import load_alternative_source_registry
from smr_phase131_eastmoney_financial_adapter import build_eastmoney_financial_adapter
from smr_phase131_szse_disclosure_adapter import build_szse_disclosure_adapter
from smr_phase131_irm_interaction_adapter import build_irm_interaction_adapter
from smr_phase131_company_ir_adapter import build_company_ir_adapter
from smr_phase131_known_url_integration_loader import build_known_url_integration
from smr_phase131_alternative_source_normalizer import build_alternative_source_normalizer
from smr_phase131_alternative_source_quality_gate import build_alternative_source_quality_gate
from smr_phase131_hard_data_integration_update import build_hard_data_integration_update
from smr_phase131_watchlist_coverage_update import build_watchlist_coverage_update
from smr_phase131_daily_brief_integration_update import build_daily_brief_integration_update
from smr_phase131_signal_effectiveness_update import build_signal_effectiveness_update
from smr_phase131_health_gap_register_update import build_health_gap_register_update
from smr_phase131_integration_decision_builder import build_integration_decision
from smr_phase131_integration_board import build_integration_board
from smr_phase131_integration_brief import build_integration_brief_md
from smr_phase131_integration_memory import build_integration_memory
from smr_phase131_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase131_backlog_update import build_backlog_update

class TestPhase131Config(unittest.TestCase):
    def test_loads(self): c=load_config();self.assertEqual(c["phase"],"phase131")
    def test_research_only(self): self.assertTrue(load_config()["research_only"])
    def test_target_ticker(self): self.assertEqual(load_config()["target_ticker"],"300394.SZ")

class TestPhase131DomainRegistry(unittest.TestCase):
    def test_has_domains(self): self.assertGreater(build_domain_registry()["phase131_domain_registry"]["total"],15)

class TestPhase131Phase130ResolutionLoader(unittest.TestCase):
    def test_ready(self): self.assertTrue(load_phase130_resolution()["phase131_phase130_resolution_loader"]["ready_for_integration"])

class TestPhase131AlternativeSourceRegistryLoader(unittest.TestCase):
    def test_has_sources(self): self.assertGreater(load_alternative_source_registry()["phase131_alternative_source_registry_loader"]["total"],0)
    def test_has_financial(self): self.assertGreater(len(load_alternative_source_registry()['phase131_alternative_source_registry_loader']['financial_sources']),0)

class TestPhase131EastmoneyFinancialAdapter(unittest.TestCase):
    def test_feasible(self): self.assertTrue(build_eastmoney_financial_adapter()["phase131_eastmoney_financial_adapter"]["300394_financial_data_feasible"])
    def test_no_org_id(self): self.assertTrue(build_eastmoney_financial_adapter()["phase131_eastmoney_financial_adapter"]["no_cninfo_org_id_needed"])

class TestPhase131SzseDisclosureAdapter(unittest.TestCase):
    def test_builds(self): self.assertTrue(build_szse_disclosure_adapter()["phase131_szse_disclosure_adapter"]["adapter"]["data_available"])

class TestPhase131IrmInteractionAdapter(unittest.TestCase):
    def test_builds(self): self.assertTrue(build_irm_interaction_adapter()["phase131_irm_interaction_adapter"]["adapter"]["data_available"])

class TestPhase131CompanyIrAdapter(unittest.TestCase):
    def test_builds(self): self.assertIn("requires_owner_url_verification",build_company_ir_adapter()["phase131_company_ir_adapter"])

class TestPhase131KnownUrlIntegrationLoader(unittest.TestCase):
    def test_has_urls(self): self.assertGreater(build_known_url_integration()["phase131_known_url_integration_loader"]["total"],0)

class TestPhase131AlternativeSourceNormalizer(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_alternative_source_normalizer()["phase131_alternative_source_normalizer"]["ready_for_metric_pipeline"])

class TestPhase131AlternativeSourceQualityGate(unittest.TestCase):
    def test_pass(self):
        r=build_alternative_source_quality_gate()
        self.assertEqual(r["phase131_alternative_source_quality_gate"]["overall"],"pass")
        self.assertEqual(r["phase131_alternative_source_quality_gate"]["violations"],0)

class TestPhase131HardDataIntegrationUpdate(unittest.TestCase):
    def test_all_8(self): self.assertTrue(build_hard_data_integration_update()["phase131_hard_data_integration_update"]["all_8_tickers_covered"])

class TestPhase131WatchlistCoverageUpdate(unittest.TestCase):
    def test_all_8(self): self.assertEqual(build_watchlist_coverage_update()["phase131_watchlist_coverage_update"]["covered_count"],8)
    def test_no_trade(self): r=build_watchlist_coverage_update();self.assertEqual(r["phase131_watchlist_coverage_update"]["pending_created"],0)

class TestPhase131DailyBriefIntegrationUpdate(unittest.TestCase):
    def test_added(self): self.assertTrue(build_daily_brief_integration_update()["phase131_daily_brief_integration_update"]["300394_added_to_daily_monitoring"])

class TestPhase131SignalEffectivenessUpdate(unittest.TestCase):
    def test_added(self): self.assertTrue(build_signal_effectiveness_update()["phase131_signal_effectiveness_update"]["300394_added_to_signal_sample"])

class TestPhase131HealthGapRegisterUpdate(unittest.TestCase):
    def test_resolved(self): self.assertTrue(build_health_gap_register_update()["phase131_health_gap_register_update"]["300394_blocker_resolved"])

class TestPhase131IntegrationDecisionBuilder(unittest.TestCase):
    def test_all_8(self): self.assertTrue(build_integration_decision()["phase131_integration_decision_builder"]["all_8_tickers_covered"])
    def test_not_trade(self): self.assertTrue(build_integration_decision()["phase131_integration_decision_builder"]["not_a_trade_recommendation"])

class TestPhase131IntegrationBoard(unittest.TestCase):
    def test_not_trade(self): self.assertTrue(build_integration_board()["phase131_integration_board"]["not_trade_board"])

class TestPhase131IntegrationBrief(unittest.TestCase):
    def test_has_content(self): self.assertIn("300394",build_integration_brief_md())

class TestPhase131IntegrationMemory(unittest.TestCase):
    def test_gitignored(self): self.assertTrue(build_integration_memory()["phase131_integration_memory"]["gitignored"])

class TestPhase131CannotConcludeGuard(unittest.TestCase):
    def test_pass(self):
        r=run_cannot_conclude_guard()
        self.assertEqual(r["phase131_cannot_conclude_guard"]["overall"],"pass")
        self.assertEqual(r["phase131_cannot_conclude_guard"]["violations"],0)

class TestPhase131BacklogUpdate(unittest.TestCase):
    def test_next_phase(self): self.assertIn("phase132",build_backlog_update()["phase131_backlog_update"]["next_phase"])
    def test_coverage(self): self.assertEqual(build_backlog_update()["phase131_backlog_update"]["coverage_count"],8)

class TestPhase131RegressionGate(unittest.TestCase):
    def test_phase130_regression(self):
        from smr_phase130_cannot_conclude_guard import run_cannot_conclude_guard as g130
        self.assertEqual(g130()["phase130_cannot_conclude_guard"]["overall"],"pass")
    def test_phase129_regression(self):
        from smr_phase129_cannot_conclude_guard import run_cannot_conclude_guard as g129
        self.assertEqual(g129()["phase129_cannot_conclude_guard"]["overall"],"pass")
    def test_688041_retained(self): self.assertTrue(build_backlog_update()["phase131_backlog_update"]["688041_retained"])

if __name__=="__main__":
    unittest.main()
