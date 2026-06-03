import unittest,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
from smr_phase135_config import load_config
from smr_phase135_domain_registry import build_domain_registry
from smr_phase135_phase134_console_loader import load_phase134_console
from smr_phase135_console_feedback_schema import build_console_feedback_schema
from smr_phase135_ticker_card_feedback_intake import build_ticker_card_feedback_intake
from smr_phase135_owner_action_feedback_intake import build_owner_action_feedback_intake
from smr_phase135_daily_brief_feedback_intake import build_daily_brief_feedback_intake
from smr_phase135_source_signal_feedback_intake import build_source_signal_feedback_intake
from smr_phase135_gap_risk_feedback_intake import build_gap_risk_feedback_intake
from smr_phase135_seasonal_insight_feedback_intake import build_seasonal_insight_feedback_intake
from smr_phase135_feedback_validator import run_feedback_validator
from smr_phase135_feedback_entity_linker import build_feedback_entity_linker
from smr_phase135_research_priority_feedback_adapter import build_research_priority_feedback_adapter
from smr_phase135_brief_layout_feedback_adapter import build_brief_layout_feedback_adapter
from smr_phase135_source_signal_weight_feedback_adapter import build_source_signal_weight_feedback_adapter
from smr_phase135_deep_dive_task_feedback_adapter import build_deep_dive_task_feedback_adapter
from smr_phase135_research_loop_tuning_recommendation import build_research_loop_tuning_recommendation
from smr_phase135_feedback_impact_board import build_feedback_impact_board
from smr_phase135_console_feedback_template import build_console_feedback_template
from smr_phase135_feedback_integration_memory import build_feedback_integration_memory
from smr_phase135_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase135_backlog_update import build_backlog_update

class TestPhase135Config(unittest.TestCase):
    def test_loads(self): self.assertEqual(load_config()["phase"],"phase135")
    def test_research_only(self): self.assertTrue(load_config()["research_only"])
    def test_feedback_enabled(self): self.assertTrue(load_config()["owner_feedback_integration_enabled"])
    def test_loop_tuning(self): self.assertTrue(load_config()["research_loop_tuning_enabled"])
    def test_feedback_types(self): self.assertGreaterEqual(len(load_config()["feedback_types"]),10)
    def test_safety(self):
        s=load_config()["safety"];self.assertFalse(s["mock"]);self.assertFalse(s["trade_recommendation_allowed"])

class TestPhase135DomainRegistry(unittest.TestCase):
    def test_has_domains(self): self.assertGreater(build_domain_registry()["phase135_domain_registry"]["total"],15)
    def test_all_research_only(self): self.assertTrue(build_domain_registry()["phase135_domain_registry"]["all_research_only"])

class TestPhase135Phase134ConsoleLoader(unittest.TestCase):
    def test_loaded(self): self.assertTrue(load_phase134_console()["phase135_phase134_console_loader"]["status"]["phase134_loaded"])
    def test_all_8(self): self.assertTrue(load_phase134_console()["phase135_phase134_console_loader"]["status"]["all_8_full_coverage"])

class TestPhase135FeedbackSchema(unittest.TestCase):
    def test_types(self): self.assertGreaterEqual(len(build_console_feedback_schema()["phase135_console_feedback_schema"]["schema"]["feedback_types"]),10)
    def test_empty_ready(self): self.assertTrue(build_console_feedback_schema()["phase135_console_feedback_schema"]["schema"]["empty_feedback_ready"])

class TestPhase135TickerCardFeedbackIntake(unittest.TestCase):
    def test_feedbacks(self): self.assertGreaterEqual(build_ticker_card_feedback_intake()["phase135_ticker_card_feedback_intake"]["total"],1)
    def test_empty_ready(self): self.assertTrue(build_ticker_card_feedback_intake()["phase135_ticker_card_feedback_intake"]["empty_feedback_ready"])

class TestPhase135OwnerActionFeedbackIntake(unittest.TestCase):
    def test_empty_ready(self): self.assertTrue(build_owner_action_feedback_intake()["phase135_owner_action_feedback_intake"]["empty_feedback_ready"])

class TestPhase135DailyBriefFeedbackIntake(unittest.TestCase):
    def test_empty_ready(self): self.assertTrue(build_daily_brief_feedback_intake()["phase135_daily_brief_feedback_intake"]["empty_feedback_ready"])

class TestPhase135SourceSignalFeedbackIntake(unittest.TestCase):
    def test_feedbacks(self): self.assertGreaterEqual(build_source_signal_feedback_intake()["phase135_source_signal_feedback_intake"]["total"],1)

class TestPhase135GapRiskFeedbackIntake(unittest.TestCase):
    def test_feedbacks(self): self.assertGreaterEqual(build_gap_risk_feedback_intake()["phase135_gap_risk_feedback_intake"]["total"],1)

class TestPhase135SeasonalInsightFeedbackIntake(unittest.TestCase):
    def test_empty_ready(self): self.assertTrue(build_seasonal_insight_feedback_intake()["phase135_seasonal_insight_feedback_intake"]["empty_feedback_ready"])

class TestPhase135FeedbackValidator(unittest.TestCase):
    def test_all_checked(self): self.assertGreaterEqual(run_feedback_validator()["phase135_feedback_validator"]["all_feedbacks_checked"],6)
    def test_valid_count(self): self.assertGreaterEqual(run_feedback_validator()["phase135_feedback_validator"]["valid_feedback_count"],6)
    def test_no_trade(self): self.assertEqual(run_feedback_validator()["phase135_feedback_validator"]["rejected_trade_like_feedback"],0)

class TestPhase135FeedbackEntityLinker(unittest.TestCase):
    def test_links(self): self.assertGreaterEqual(build_feedback_entity_linker()["phase135_feedback_entity_linker"]["total_linked"],6)

class TestPhase135ResearchPriorityFeedbackAdapter(unittest.TestCase):
    def test_not_trade(self): self.assertTrue(build_research_priority_feedback_adapter()["phase135_research_priority_feedback_adapter"]["not_trade_signal"])
    def test_adjustments(self): self.assertGreaterEqual(build_research_priority_feedback_adapter()["phase135_research_priority_feedback_adapter"]["total_adjusted"],1)

class TestPhase135BriefLayoutFeedbackAdapter(unittest.TestCase):
    def test_not_trade(self): self.assertTrue(build_brief_layout_feedback_adapter()["phase135_brief_layout_feedback_adapter"]["not_trade_signal"])

class TestPhase135SourceSignalWeightFeedbackAdapter(unittest.TestCase):
    def test_not_trade(self): self.assertTrue(build_source_signal_weight_feedback_adapter()["phase135_source_signal_weight_feedback_adapter"]["not_trade_signal"])

class TestPhase135DeepDiveTaskFeedbackAdapter(unittest.TestCase):
    def test_no_trade_actions(self): self.assertEqual(build_deep_dive_task_feedback_adapter()["phase135_deep_dive_task_feedback_adapter"]["trade_actions"],0)
    def test_not_trade(self): self.assertTrue(build_deep_dive_task_feedback_adapter()["phase135_deep_dive_task_feedback_adapter"]["not_trade_signal"])

class TestPhase135ResearchLoopTuning(unittest.TestCase):
    def test_all_not_trade(self): self.assertTrue(build_research_loop_tuning_recommendation()["phase135_research_loop_tuning_recommendation"]["all_not_trade"])

class TestPhase135FeedbackImpactBoard(unittest.TestCase):
    def test_not_trade(self): self.assertTrue(build_feedback_impact_board()["phase135_feedback_impact_board"]["not_trade_signal"])

class TestPhase135FeedbackTemplate(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_console_feedback_template()["phase135_console_feedback_template"]["ready_for_owner_use"])

class TestPhase135FeedbackMemory(unittest.TestCase):
    def test_records(self): self.assertGreaterEqual(build_feedback_integration_memory()["phase135_feedback_integration_memory"]["records_written"],3)
    def test_path_ignored(self): self.assertTrue(build_feedback_integration_memory()["phase135_feedback_integration_memory"]["memory_path_ignored"])

class TestPhase135CannotConcludeGuard(unittest.TestCase):
    def test_pass(self): self.assertEqual(run_cannot_conclude_guard()["phase135_cannot_conclude_guard"]["overall"],"pass")
    def test_violations_0(self): self.assertEqual(run_cannot_conclude_guard()["phase135_cannot_conclude_guard"]["violations"],0)

class TestPhase135BacklogUpdate(unittest.TestCase):
    def test_feedback_deployed(self): self.assertIn("feedback",build_backlog_update()["phase135_backlog_update"]["phase135_status"])
    def test_next_phase(self): self.assertIn("phase136",build_backlog_update()["phase135_backlog_update"]["next_phase"])

class TestPhase135RegressionGate(unittest.TestCase):
    def test_phase134_regression(self):
        r=load_phase134_console()["phase135_phase134_console_loader"]["status"]
        self.assertTrue(r["phase134_loaded"]);self.assertTrue(r["console_active"]);self.assertTrue(r["all_8_full_coverage"])

if __name__=="__main__":
    unittest.main()
