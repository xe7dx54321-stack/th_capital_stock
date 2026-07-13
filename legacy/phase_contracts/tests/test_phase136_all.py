import unittest,json,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "08_scripts" / "lib"))
from smr_phase136_config import load_config
from smr_phase136_deep_dive_workflow_domain_registry import build_domain_registry
from smr_phase136_phase135_feedback_task_loader import load_phase135_feedback_tasks
from smr_phase136_deep_dive_task_schema import build_deep_dive_task_schema
from smr_phase136_task_prioritizer import build_task_prioritizer
from smr_phase136_task_entity_linker import build_task_entity_linker
from smr_phase136_evidence_requirement_builder import build_evidence_requirement
from smr_phase136_source_plan_builder import build_source_plan
from smr_phase136_research_question_generator import build_research_questions
from smr_phase136_execution_plan_builder import build_execution_plan
from smr_phase136_evidence_checklist import build_evidence_checklist
from smr_phase136_deep_dive_research_packet_builder import build_deep_dive_research_packet
from smr_phase136_task_status_tracker import build_task_status_tracker
from smr_phase136_console_integration_update import build_console_integration_update
from smr_phase136_daily_brief_integration_update import build_daily_brief_integration_update
from smr_phase136_feedback_memory_integration_update import build_feedback_memory_integration_update
from smr_phase136_decision_journal_candidate_update import build_decision_journal_candidate_update
from smr_phase136_deep_dive_quality_gate import run_deep_dive_quality_gate
from smr_phase136_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase136_backlog_update import build_backlog_update

class TestPhase136Config(unittest.TestCase):
    def test_loads(self): self.assertEqual(load_config()["phase"],"phase136")
    def test_research_only(self): self.assertTrue(load_config()["research_only"])
    def test_deep_dive_enabled(self): self.assertTrue(load_config()["deep_dive_workflow_enabled"])
    def test_safety(self): s=load_config()["safety"];self.assertFalse(s["mock"]);self.assertFalse(s["trade_recommendation_allowed"])

class TestPhase136DomainRegistry(unittest.TestCase):
    def test_has_domains(self): self.assertGreater(build_domain_registry()["phase136_deep_dive_workflow_domain_registry"]["total"],15)
    def test_all_research_only(self): self.assertTrue(build_domain_registry()["phase136_deep_dive_workflow_domain_registry"]["all_research_only"])

class TestPhase136Phase135Loader(unittest.TestCase):
    def test_loaded(self): self.assertTrue(load_phase135_feedback_tasks()["phase136_phase135_feedback_task_loader"]["status"]["phase135_loaded"])
    def test_tasks(self): self.assertGreaterEqual(len(load_phase135_feedback_tasks()["phase136_phase135_feedback_task_loader"]["tasks"]),1)

class TestPhase136TaskSchema(unittest.TestCase):
    def test_types(self): self.assertGreaterEqual(len(build_deep_dive_task_schema()["phase136_deep_dive_task_schema"]["task_types"]),6)

class TestPhase136TaskPrioritizer(unittest.TestCase):
    def test_tasks(self): self.assertGreaterEqual(build_task_prioritizer()["phase136_task_prioritizer"]["total"],2)
    def test_all_not_trade(self): self.assertTrue(build_task_prioritizer()["phase136_task_prioritizer"]["all_not_trade"])

class TestPhase136TaskEntityLinker(unittest.TestCase):
    def test_links(self): self.assertGreaterEqual(build_task_entity_linker()["phase136_task_entity_linker"]["total"],2)

class TestPhase136EvidenceRequirement(unittest.TestCase):
    def test_tasks(self): self.assertGreaterEqual(build_evidence_requirement()["phase136_evidence_requirement_builder"]["total_tasks"],2)
    def test_not_advice(self): self.assertTrue(build_evidence_requirement()["phase136_evidence_requirement_builder"]["all_evidence_not_investment_advice"])

class TestPhase136SourcePlan(unittest.TestCase):
    def test_plans(self): self.assertGreaterEqual(build_source_plan()["phase136_source_plan_builder"]["total_plans"],2)
    def test_all_not_trade(self): self.assertTrue(build_source_plan()["phase136_source_plan_builder"]["all_not_trade"])

class TestPhase136ResearchQuestions(unittest.TestCase):
    def test_tasks(self): self.assertGreaterEqual(build_research_questions()["phase136_research_question_generator"]["total_tasks"],2)

class TestPhase136ExecutionPlan(unittest.TestCase):
    def test_tasks(self): self.assertGreaterEqual(build_execution_plan()["phase136_execution_plan_builder"]["total_tasks"],2)

class TestPhase136EvidenceChecklist(unittest.TestCase):
    def test_tasks(self): self.assertGreaterEqual(build_evidence_checklist()["phase136_evidence_checklist"]["total_tasks"],2)
    def test_all_not_trade(self): self.assertTrue(build_evidence_checklist()["phase136_evidence_checklist"]["all_not_trade"])

class TestPhase136ResearchPacket(unittest.TestCase):
    def test_packets(self): self.assertGreaterEqual(build_deep_dive_research_packet()["phase136_deep_dive_research_packet_builder"]["total"],2)
    def test_all_not_trade(self): self.assertTrue(build_deep_dive_research_packet()["phase136_deep_dive_research_packet_builder"]["all_not_trade"])

class TestPhase136TaskStatusTracker(unittest.TestCase):
    def test_tasks(self): self.assertGreaterEqual(build_task_status_tracker()["phase136_task_status_tracker"]["total"],2)
    def test_all_not_trade(self): self.assertTrue(build_task_status_tracker()["phase136_task_status_tracker"]["all_not_trade"])

class TestPhase136ConsoleIntegration(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_console_integration_update()["phase136_console_integration_update"]["ready_for_console_refresh"])

class TestPhase136DailyBriefIntegration(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_daily_brief_integration_update()["phase136_daily_brief_integration_update"]["ready_for_brief_refresh"])

class TestPhase136FeedbackMemoryIntegration(unittest.TestCase):
    def test_records(self): self.assertGreaterEqual(build_feedback_memory_integration_update()["phase136_feedback_memory_integration_update"]["total"],2)
    def test_path_ignored(self): self.assertTrue(build_feedback_memory_integration_update()["phase136_feedback_memory_integration_update"]["memory_path_ignored"])

class TestPhase136DecisionJournal(unittest.TestCase):
    def test_candidates(self): self.assertGreaterEqual(build_decision_journal_candidate_update()["phase136_decision_journal_candidate_update"]["total"],1)
    def test_all_not_trade(self): self.assertTrue(build_decision_journal_candidate_update()["phase136_decision_journal_candidate_update"]["all_not_trade"])

class TestPhase136QualityGate(unittest.TestCase):
    def test_pass(self): self.assertEqual(run_deep_dive_quality_gate()["phase136_deep_dive_quality_gate"]["overall"],"pass")
    def test_violations_0(self): self.assertEqual(run_deep_dive_quality_gate()["phase136_deep_dive_quality_gate"]["violations"],0)

class TestPhase136CannotConcludeGuard(unittest.TestCase):
    def test_pass(self): self.assertEqual(run_cannot_conclude_guard()["phase136_cannot_conclude_guard"]["overall"],"pass")
    def test_violations_0(self): self.assertEqual(run_cannot_conclude_guard()["phase136_cannot_conclude_guard"]["violations"],0)

class TestPhase136BacklogUpdate(unittest.TestCase):
    def test_deployed(self): self.assertIn("deep_dive",build_backlog_update()["phase136_backlog_update"]["phase136_status"])
    def test_next_phase(self): self.assertIn("phase137",build_backlog_update()["phase136_backlog_update"]["next_phase"])

class TestPhase136RegressionGate(unittest.TestCase):
    def test_phase135_regression(self):
        r=load_phase135_feedback_tasks()["phase136_phase135_feedback_task_loader"]["status"]
        self.assertTrue(r["phase135_loaded"]);self.assertTrue(r["all_feedback_not_trade"])

if __name__=="__main__":
    unittest.main()
