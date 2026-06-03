import unittest,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
from smr_phase137_config import load_config
from smr_phase137_domain_registry import build_domain_registry
from smr_phase137_phase136_task_loader import load_phase136_tasks
from smr_phase137_task_execution_scope_resolver import build_execution_scope_resolver
from smr_phase137_existing_evidence_loader import build_existing_evidence_loader
from smr_phase137_hard_data_evidence_updater import build_hard_data_evidence_updater
from smr_phase137_valuation_evidence_updater import build_valuation_evidence_updater
from smr_phase137_source_evidence_updater import build_source_evidence_updater
from smr_phase137_catalyst_opportunity_evidence_updater import build_catalyst_opportunity_evidence_updater
from smr_phase137_risk_gap_evidence_updater import build_risk_gap_evidence_updater
from smr_phase137_manual_confirmation_tracker import build_manual_confirmation_tracker
from smr_phase137_task_finding_builder import build_task_findings
from smr_phase137_evidence_delta_classifier import build_evidence_delta_classifier
from smr_phase137_task_status_closeout_builder import build_task_status_closeout
from smr_phase137_updated_research_packet_builder import build_updated_research_packet
from smr_phase137_console_integration_update import build_console_integration_update
from smr_phase137_daily_brief_integration_update import build_daily_brief_integration_update
from smr_phase137_feedback_memory_integration_update import build_feedback_memory_integration_update
from smr_phase137_decision_journal_update_candidate import build_decision_journal_update_candidate
from smr_phase137_evidence_memory_writer import build_evidence_memory
from smr_phase137_quality_gate import run_quality_gate
from smr_phase137_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase137_backlog_update import build_backlog_update

class TestPhase137Config(unittest.TestCase):
    def test_loads(self): self.assertEqual(load_config()["phase"],"phase137")
    def test_research_only(self): self.assertTrue(load_config()["research_only"])
    def test_execution_enabled(self): self.assertTrue(load_config()["deep_dive_execution_enabled"])
    def test_safety(self): s=load_config()["safety"];self.assertFalse(s["mock"]);self.assertFalse(s["trade_recommendation_allowed"])

class TestPhase137DomainRegistry(unittest.TestCase):
    def test_has_domains(self): self.assertGreater(build_domain_registry()["phase137_domain_registry"]["total"],18)
    def test_all_research_only(self): self.assertTrue(build_domain_registry()["phase137_domain_registry"]["all_research_only"])

class TestPhase137Phase136Loader(unittest.TestCase):
    def test_tasks(self): self.assertEqual(load_phase136_tasks()["phase137_phase136_task_loader"]["total"],3)
    def test_all_not_trade(self): self.assertTrue(load_phase136_tasks()["phase137_phase136_task_loader"]["all_not_trade"])

class TestPhase137ScopeResolver(unittest.TestCase):
    def test_scopes(self): self.assertEqual(build_execution_scope_resolver()["phase137_task_execution_scope_resolver"]["total"],3)

class TestPhase137ExistingEvidence(unittest.TestCase):
    def test_tasks(self): self.assertEqual(build_existing_evidence_loader()["phase137_existing_evidence_loader"]["total_tasks"],3)

class TestPhase137HardEvidence(unittest.TestCase):
    def test_tasks(self): self.assertEqual(build_hard_data_evidence_updater()["phase137_hard_data_evidence_updater"]["total"],3)
    def test_not_trade(self): self.assertTrue(build_hard_data_evidence_updater()["phase137_hard_data_evidence_updater"]["all_not_trade"])

class TestPhase137ValuationEvidence(unittest.TestCase):
    def test_tasks(self): self.assertEqual(build_valuation_evidence_updater()["phase137_valuation_evidence_updater"]["total"],2)

class TestPhase137SourceEvidence(unittest.TestCase):
    def test_tasks(self): self.assertEqual(build_source_evidence_updater()["phase137_source_evidence_updater"]["total"],3)

class TestPhase137CatalystEvidence(unittest.TestCase):
    def test_tasks(self): self.assertEqual(build_catalyst_opportunity_evidence_updater()["phase137_catalyst_opportunity_evidence_updater"]["total"],3)

class TestPhase137RiskGapEvidence(unittest.TestCase):
    def test_tasks(self): self.assertEqual(build_risk_gap_evidence_updater()["phase137_risk_gap_evidence_updater"]["total"],3)

class TestPhase137ManualConfirmation(unittest.TestCase):
    def test_items(self): self.assertGreaterEqual(build_manual_confirmation_tracker()["phase137_manual_confirmation_tracker"]["total"],3)

class TestPhase137Findings(unittest.TestCase):
    def test_tasks(self): self.assertEqual(build_task_findings()["phase137_task_finding_builder"]["total_tasks"],3)
    def test_all_not_trade(self): self.assertTrue(build_task_findings()["phase137_task_finding_builder"]["all_not_trade"])

class TestPhase137DeltaClassifier(unittest.TestCase):
    def test_tasks(self): self.assertEqual(build_evidence_delta_classifier()["phase137_evidence_delta_classifier"]["total"],3)

class TestPhase137Closeout(unittest.TestCase):
    def test_tasks(self): self.assertEqual(build_task_status_closeout()["phase137_task_status_closeout_builder"]["total"],3)
    def test_all_not_trade(self): self.assertTrue(build_task_status_closeout()["phase137_task_status_closeout_builder"]["all_not_trade"])

class TestPhase137UpdatedPacket(unittest.TestCase):
    def test_packets(self): self.assertEqual(build_updated_research_packet()["phase137_updated_research_packet_builder"]["total"],3)

class TestPhase137Console(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_console_integration_update()["phase137_console_integration_update"]["ready"])

class TestPhase137DailyBrief(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_daily_brief_integration_update()["phase137_daily_brief_integration_update"]["ready"])

class TestPhase137FeedbackMemory(unittest.TestCase):
    def test_records(self): self.assertEqual(build_feedback_memory_integration_update()["phase137_feedback_memory_integration_update"]["total"],3)

class TestPhase137Decision(unittest.TestCase):
    def test_candidates(self): self.assertEqual(build_decision_journal_update_candidate()["phase137_decision_journal_update_candidate"]["total"],2)

class TestPhase137EvidenceMemory(unittest.TestCase):
    def test_records(self): self.assertEqual(build_evidence_memory()["phase137_evidence_memory_writer"]["total"],4)

class TestPhase137QualityGate(unittest.TestCase):
    def test_pass(self): self.assertEqual(run_quality_gate()["phase137_quality_gate"]["overall"],"pass")
    def test_violations_0(self): self.assertEqual(run_quality_gate()["phase137_quality_gate"]["violations"],0)

class TestPhase137Guard(unittest.TestCase):
    def test_pass(self): self.assertEqual(run_cannot_conclude_guard()["phase137_cannot_conclude_guard"]["overall"],"pass")

class TestPhase137Backlog(unittest.TestCase):
    def test_executed(self): self.assertIn("execution",build_backlog_update()["phase137_backlog_update"]["phase137_status"])
    def test_next(self): self.assertIn("phase138",build_backlog_update()["phase137_backlog_update"]["next_phase"])

class TestPhase137Regression(unittest.TestCase):
    def test_phase136_regression(self):
        r=load_phase136_tasks()["phase137_phase136_task_loader"]
        self.assertEqual(r["total"],3);self.assertTrue(r["all_not_trade"])

if __name__=="__main__":
    unittest.main()
