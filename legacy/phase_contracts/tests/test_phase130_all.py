import unittest,json,sys,os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "08_scripts" / "lib"))

from smr_phase130_config import load_config
from smr_phase130_domain_registry import build_domain_registry
from smr_phase130_historical_blocker_loader import load_historical_blocker
from smr_phase130_identity_evidence_pack import build_identity_evidence_pack
from smr_phase130_cninfo_candidate_registry import build_cninfo_candidate_registry
from smr_phase130_cninfo_verification_runner import run_cninfo_verification
from smr_phase130_szse_disclosure_fallback import build_szse_disclosure_fallback
from smr_phase130_irm_interaction_fallback import build_irm_interaction_fallback
from smr_phase130_company_ir_loader import build_company_ir_loader
from smr_phase130_known_url_validator import run_known_url_validation
from smr_phase130_manual_url_template import build_manual_url_template
from smr_phase130_alternative_disclosure_registry import build_alternative_disclosure_registry
from smr_phase130_source_equivalence_scorer import build_source_equivalence_scorer
from smr_phase130_disclosure_coverage_classifier import classify_disclosure_coverage
from smr_phase130_hard_data_readiness import build_hard_data_readiness
from smr_phase130_watchlist_status_update import build_watchlist_status_update
from smr_phase130_gap_closeout_report import build_gap_closeout_report
from smr_phase130_manual_action_template import build_manual_action_template
from smr_phase130_resolution_decision_report import build_resolution_decision_report
from smr_phase130_integration_update import build_integration_update
from smr_phase130_resolution_board import build_resolution_board
from smr_phase130_resolution_brief import build_resolution_brief_md
from smr_phase130_resolution_memory import build_resolution_memory
from smr_phase130_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase130_backlog_update import build_backlog_update

class TestPhase130Config(unittest.TestCase):
    def test_loads(self): c=load_config();self.assertEqual(c["phase"],"phase130")
    def test_research_only(self): self.assertTrue(load_config()["research_only"])
    def test_ticker(self): self.assertEqual(load_config()["resolution_target"],"300394.SZ")
    def test_safety(self): s=load_config()["safety"];self.assertFalse(s["mock"]);self.assertFalse(s["fixture"])

class TestPhase130DomainRegistry(unittest.TestCase):
    def test_has_domains(self): self.assertGreater(build_domain_registry()["phase130_domain_registry"]["total"],15)

class TestPhase130HistoricalBlockerLoader(unittest.TestCase):
    def test_ticker(self):
        r=load_historical_blocker()
        self.assertEqual(r["phase130_historical_blocker_loader"]["ticker"],"300394.SZ")
    def test_first_attempt(self):
        r=load_historical_blocker()
        self.assertTrue(r["phase130_historical_blocker_loader"]["this_is_the_first_resolution_attempt"])

class TestPhase130IdentityEvidencePack(unittest.TestCase):
    def test_cninfo_unavailable(self):
        r=build_identity_evidence_pack()
        self.assertTrue(r["phase130_identity_evidence_pack"]["cninfo_direct_unavailable"])
    def test_alternative_available(self):
        r=build_identity_evidence_pack()
        self.assertTrue(r["phase130_identity_evidence_pack"]["alternative_paths_available"])

class TestPhase130CninfoCandidateRegistry(unittest.TestCase):
    def test_no_confirmed_org_id(self):
        r=build_cninfo_candidate_registry()
        self.assertTrue(r["phase130_cninfo_candidate_registry"]["no_confirmed_org_id"])
    def test_has_candidates(self):
        r=build_cninfo_candidate_registry()
        self.assertGreater(r["phase130_cninfo_candidate_registry"]["total"],0)

class TestPhase130CninfoVerificationRunner(unittest.TestCase):
    def test_skip_network(self):
        r=run_cninfo_verification(skip_network=True)
        self.assertFalse(r["phase130_cninfo_verification_runner"]["org_id_confirmed"])
    def test_execute(self):
        r=run_cninfo_verification(skip_network=False)
        self.assertFalse(r["phase130_cninfo_verification_runner"]["org_id_confirmed"])

class TestPhase130SzseDisclosureFallback(unittest.TestCase):
    def test_has_sources(self): self.assertGreater(build_szse_disclosure_fallback()["phase130_szse_disclosure_fallback"]["total"],0)

class TestPhase130IrmInteractionFallback(unittest.TestCase):
    def test_has_sources(self): self.assertGreater(build_irm_interaction_fallback()["phase130_irm_interaction_fallback"]["total"],0)

class TestPhase130CompanyIrLoader(unittest.TestCase):
    def test_has_sources(self): self.assertGreater(build_company_ir_loader()["phase130_company_ir_loader"]["total"],0)

class TestPhase130KnownUrlValidator(unittest.TestCase):
    def test_skip_network(self):
        r=run_known_url_validation(skip_network=True)
        self.assertFalse(r["phase130_known_url_validator"]["browser_used"])

class TestPhase130ManualUrlTemplate(unittest.TestCase):
    def test_all_owner(self):
        r=build_manual_url_template()
        self.assertTrue(r["phase130_manual_url_template"]["all_require_owner_action"])

class TestPhase130AlternativeDisclosureRegistry(unittest.TestCase):
    def test_all_free(self):
        r=build_alternative_disclosure_registry()
        self.assertTrue(r["phase130_alternative_disclosure_registry"]["all_free_no_key"])

class TestPhase130SourceEquivalenceScorer(unittest.TestCase):
    def test_has_high(self):
        r=build_source_equivalence_scorer()
        self.assertGreater(r["phase130_source_equivalence_scorer"]["high_equivalence"],0)

class TestPhase130DisclosureCoverageClassifier(unittest.TestCase):
    def test_financial_feasible(self):
        r=classify_disclosure_coverage()
        self.assertTrue(r["phase130_disclosure_coverage_classifier"]["financial_data_feasible"])

class TestPhase130HardDataReadiness(unittest.TestCase):
    def test_ready(self):
        r=build_hard_data_readiness()
        self.assertTrue(r["phase130_hard_data_readiness"]["financial_data_feasible"])

class TestPhase130WatchlistStatusUpdate(unittest.TestCase):
    def test_no_trading(self):
        r=build_watchlist_status_update()
        self.assertEqual(r["phase130_watchlist_status_update"]["pending_created"],0)
        self.assertEqual(r["phase130_watchlist_status_update"]["paper_order_created"],0)

class TestPhase130GapCloseoutReport(unittest.TestCase):
    def test_partially_resolved(self):
        r=build_gap_closeout_report()
        self.assertEqual(r["phase130_gap_closeout_report"]["blocker_status"],"partially_resolved")

class TestPhase130ManualActionTemplate(unittest.TestCase):
    def test_owner_required(self):
        r=build_manual_action_template()
        self.assertTrue(r["phase130_manual_action_template"]["all_require_owner_action"])

class TestPhase130ResolutionDecisionReport(unittest.TestCase):
    def test_not_trade(self):
        r=build_resolution_decision_report()
        self.assertTrue(r["phase130_resolution_decision_report"]["not_a_trade_recommendation"])

class TestPhase130IntegrationUpdate(unittest.TestCase):
    def test_phases_updated(self):
        r=build_integration_update()
        self.assertIn("phase82",r["phase130_integration_update"]["phases_updated"])

class TestPhase130ResolutionBoard(unittest.TestCase):
    def test_not_trade(self):
        r=build_resolution_board()
        self.assertTrue(r["phase130_resolution_board"]["not_trade_board"])

class TestPhase130ResolutionBrief(unittest.TestCase):
    def test_has_content(self):
        md=build_resolution_brief_md()
        self.assertIn("300394",md)

class TestPhase130ResolutionMemory(unittest.TestCase):
    def test_gitignored(self):
        self.assertTrue(build_resolution_memory()["phase130_resolution_memory"]["gitignored"])

class TestPhase130CannotConcludeGuard(unittest.TestCase):
    def test_pass(self):
        r=run_cannot_conclude_guard()
        self.assertEqual(r["phase130_cannot_conclude_guard"]["overall"],"pass")
        self.assertEqual(r["phase130_cannot_conclude_guard"]["violations"],0)

class TestPhase130BacklogUpdate(unittest.TestCase):
    def test_next_phase(self):
        self.assertIn("phase131",build_backlog_update()["phase130_backlog_update"]["next_phase"])
    def test_300394_retained(self):
        self.assertTrue(build_backlog_update()["phase130_backlog_update"]["300394_retained"])

class TestPhase130RegressionGate(unittest.TestCase):
    def test_phase129_regression(self):
        from smr_phase129_cannot_conclude_guard import run_cannot_conclude_guard as g129
        self.assertEqual(g129()["phase129_cannot_conclude_guard"]["overall"],"pass")
    def test_phase128_regression(self):
        from smr_phase128_cannot_conclude_guard import run_cannot_conclude_guard as g128
        self.assertEqual(g128()["phase128_cannot_conclude_guard"]["overall"],"pass")
    def test_688041_retained(self):
        r=build_backlog_update()
        self.assertTrue(r["phase130_backlog_update"]["688041_retained"])

if __name__=="__main__":
    unittest.main()
