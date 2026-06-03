import unittest,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
from smr_phase138_config import load_config
from smr_phase138_domain_registry import build_domain_registry
from smr_phase138_phase137_execution_loader import load_phase137_execution
from smr_phase138_research_context_loader import load_research_context
from smr_phase138_ticker_thesis_schema import build_ticker_thesis_schema
from smr_phase138_thesis_entity_registry import build_thesis_entity_registry
from smr_phase138_evidence_to_thesis_linker import build_evidence_to_thesis_linker
from smr_phase138_finding_to_thesis_updater import build_finding_to_thesis_updater
from smr_phase138_thesis_status_classifier import build_thesis_status_classifier
from smr_phase138_thesis_confidence_scorer import build_thesis_confidence_scorer
from smr_phase138_contradiction_risk_linker import build_contradiction_risk_linker
from smr_phase138_thesis_change_log import build_thesis_change_log
from smr_phase138_research_memory_graph_builder import build_research_memory_graph
from smr_phase138_ticker_thesis_card_builder import build_ticker_thesis_cards
from smr_phase138_cross_ticker_theme_map import build_cross_ticker_theme_map
from smr_phase138_thesis_library_board import build_thesis_library_board
from smr_phase138_console_integration_update import build_console_integration_update
from smr_phase138_daily_brief_integration_update import build_daily_brief_integration_update
from smr_phase138_decision_journal_integration_update import build_decision_journal_integration_update
from smr_phase138_thesis_memory_writer import build_thesis_memory
from smr_phase138_quality_gate import run_quality_gate
from smr_phase138_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase138_backlog_update import build_backlog_update

class TestPhase138Config(unittest.TestCase):
    def test_loads(self): self.assertEqual(load_config()["phase"],"phase138")
    def test_research_only(self): self.assertTrue(load_config()["research_only"])
    def test_thesis_enabled(self): self.assertTrue(load_config()["thesis_library_enabled"])
    def test_safety(self): s=load_config()["safety"];self.assertFalse(s["mock"])

class TestPhase138DomainRegistry(unittest.TestCase):
    def test_has_domains(self): self.assertGreater(build_domain_registry()["phase138_domain_registry"]["total"],18)
    def test_all_research_only(self): self.assertTrue(build_domain_registry()["phase138_domain_registry"]["all_research_only"])

class TestPhase138Phase137Loader(unittest.TestCase):
    def test_tasks(self): self.assertEqual(load_phase137_execution()["phase138_phase137_execution_loader"]["total"],3)

class TestPhase138ResearchContext(unittest.TestCase):
    def test_loaded(self): self.assertTrue(load_research_context()["phase138_research_context_loader"]["context"]["all_8_full_coverage"])

class TestPhase138ThesisSchema(unittest.TestCase):
    def test_statuses(self): self.assertGreaterEqual(len(build_ticker_thesis_schema()["phase138_ticker_thesis_schema"]["schema"]["thesis_statuses"]),5)

class TestPhase138ThesisRegistry(unittest.TestCase):
    def test_count(self): self.assertEqual(build_thesis_entity_registry()["phase138_thesis_entity_registry"]["total"],8)

class TestPhase138EvidenceLinker(unittest.TestCase):
    def test_links(self): self.assertGreaterEqual(build_evidence_to_thesis_linker()["phase138_evidence_to_thesis_linker"]["total"],2)

class TestPhase138FindingUpdater(unittest.TestCase):
    def test_updates(self): self.assertGreaterEqual(build_finding_to_thesis_updater()["phase138_finding_to_thesis_updater"]["total"],2)

class TestPhase138StatusClassifier(unittest.TestCase):
    def test_total(self): self.assertEqual(build_thesis_status_classifier()["phase138_thesis_status_classifier"]["total"],8)
    def test_strengthened(self): self.assertEqual(build_thesis_status_classifier()["phase138_thesis_status_classifier"]["summary"]["thesis_strengthened"],1)

class TestPhase138ConfidenceScorer(unittest.TestCase):
    def test_scores(self): self.assertGreaterEqual(build_thesis_confidence_scorer()["phase138_thesis_confidence_scorer"]["total"],2)

class TestPhase138RiskLinker(unittest.TestCase):
    def test_items(self): self.assertGreaterEqual(build_contradiction_risk_linker()["phase138_contradiction_risk_linker"]["total"],2)

class TestPhase138ChangeLog(unittest.TestCase):
    def test_log(self): self.assertGreaterEqual(build_thesis_change_log()["phase138_thesis_change_log"]["total"],2)

class TestPhase138MemoryGraph(unittest.TestCase):
    def test_nodes(self): self.assertGreaterEqual(len(build_research_memory_graph()["phase138_research_memory_graph_builder"]["nodes"]),2)

class TestPhase138ThesisCards(unittest.TestCase):
    def test_cards(self): self.assertEqual(build_ticker_thesis_cards()["phase138_ticker_thesis_card_builder"]["total"],8)
    def test_not_trade(self): self.assertTrue(build_ticker_thesis_cards()["phase138_ticker_thesis_card_builder"]["all_not_trade"])

class TestPhase138ThemeMap(unittest.TestCase):
    def test_themes(self): self.assertGreaterEqual(build_cross_ticker_theme_map()["phase138_cross_ticker_theme_map"]["total"],2)

class TestPhase138Board(unittest.TestCase):
    def test_not_trade(self): self.assertTrue(build_thesis_library_board()["phase138_thesis_library_board"]["not_trade_signal"])

class TestPhase138Console(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_console_integration_update()["phase138_console_integration_update"]["ready"])

class TestPhase138DailyBrief(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_daily_brief_integration_update()["phase138_daily_brief_integration_update"]["ready"])

class TestPhase138Decision(unittest.TestCase):
    def test_candidates(self): self.assertGreaterEqual(build_decision_journal_integration_update()["phase138_decision_journal_integration_update"]["total"],1)

class TestPhase138ThesisMemory(unittest.TestCase):
    def test_records(self): self.assertGreaterEqual(build_thesis_memory()["phase138_thesis_memory_writer"]["total"],1)

class TestPhase138QualityGate(unittest.TestCase):
    def test_pass(self): self.assertEqual(run_quality_gate()["phase138_quality_gate"]["overall"],"pass")
    def test_violations_0(self): self.assertEqual(run_quality_gate()["phase138_quality_gate"]["violations"],0)

class TestPhase138Guard(unittest.TestCase):
    def test_pass(self): self.assertEqual(run_cannot_conclude_guard()["phase138_cannot_conclude_guard"]["overall"],"pass")

class TestPhase138Backlog(unittest.TestCase):
    def test_deployed(self): self.assertIn("thesis",build_backlog_update()["phase138_backlog_update"]["phase138_status"])
    def test_next(self): self.assertIn("phase139",build_backlog_update()["phase138_backlog_update"]["next_phase"])

class TestPhase138Regression(unittest.TestCase):
    def test_phase137_regression(self):
        r=load_phase137_execution()["phase138_phase137_execution_loader"]
        self.assertEqual(r["total"],3);self.assertTrue(r["all_not_trade"])

if __name__=="__main__":
    unittest.main()
