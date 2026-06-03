import unittest,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
from smr_phase139_config import load_config
from smr_phase139_domain_registry import build_domain_registry
from smr_phase139_phase138_thesis_loader import load_phase138_thesis
from smr_phase139_run_schedule_profile import build_run_schedule_profile
from smr_phase139_daily_research_run_plan import build_daily_research_run_plan
from smr_phase139_weekly_research_review_run_plan import build_weekly_review_plan
from smr_phase139_module_execution_planner import build_module_execution_planner
from smr_phase139_delivery_package_builder import build_delivery_package
from smr_phase139_owner_delivery_index import build_owner_delivery_index
from smr_phase139_local_notification_template import build_local_notification_template
from smr_phase139_run_history_writer import build_run_history
from smr_phase139_delivery_archive_writer import build_delivery_archive
from smr_phase139_failure_degraded_handling import build_failure_degraded_handling
from smr_phase139_delivery_quality_gate import run_delivery_quality_gate
from smr_phase139_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase139_backlog_update import build_backlog_update

class TestPhase139Config(unittest.TestCase):
    def test_loads(self): self.assertEqual(load_config()["phase"],"phase139")
    def test_research_only(self): self.assertTrue(load_config()["research_only"])
    def test_delivery_enabled(self): self.assertTrue(load_config()["scheduled_delivery_enabled"])
    def test_safety(self): s=load_config()["safety"];self.assertFalse(s["mock"])

class TestPhase139DomainRegistry(unittest.TestCase):
    def test_has_domains(self): self.assertGreater(build_domain_registry()["phase139_domain_registry"]["total"],12)
    def test_all_research_only(self): self.assertTrue(build_domain_registry()["phase139_domain_registry"]["all_research_only"])

class TestPhase139Phase138Loader(unittest.TestCase):
    def test_theses(self): self.assertEqual(load_phase138_thesis()["phase139_phase138_thesis_loader"]["theses_loaded"],8)

class TestPhase139ScheduleProfile(unittest.TestCase):
    def test_daily_modules(self): self.assertGreaterEqual(len(build_run_schedule_profile()["phase139_run_schedule_profile"]["schedule"]["daily"]["modules"]),3)
    def test_weekly_modules(self): self.assertGreaterEqual(len(build_run_schedule_profile()["phase139_run_schedule_profile"]["schedule"]["weekly"]["modules"]),3)

class TestPhase139DailyPlan(unittest.TestCase):
    def test_steps(self): self.assertGreaterEqual(len(build_daily_research_run_plan()["phase139_daily_research_run_plan"]["plan"]["steps"]),2)

class TestPhase139WeeklyPlan(unittest.TestCase):
    def test_steps(self): self.assertGreaterEqual(len(build_weekly_review_plan()["phase139_weekly_research_review_run_plan"]["plan"]["steps"]),2)

class TestPhase139ExecutionPlanner(unittest.TestCase):
    def test_modules(self): self.assertGreaterEqual(build_module_execution_planner()["phase139_module_execution_planner"]["plan"]["daily_modules"],3)

class TestPhase139DeliveryPackage(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_delivery_package()["phase139_delivery_package_builder"]["ready"])
    def test_not_trade(self): self.assertTrue(build_delivery_package()["phase139_delivery_package_builder"]["not_trade"])

class TestPhase139OwnerIndex(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_owner_delivery_index()["phase139_owner_delivery_index"]["ready"])

class TestPhase139Notification(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_local_notification_template()["phase139_local_notification_template"]["ready"])

class TestPhase139RunHistory(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_run_history()["phase139_run_history_writer"]["ready"])
    def test_path_ignored(self): self.assertTrue(build_run_history()["phase139_run_history_writer"]["history"]["path_ignored"])

class TestPhase139Archive(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_delivery_archive()["phase139_delivery_archive_writer"]["ready"])

class TestPhase139FailureHandling(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_failure_degraded_handling()["phase139_failure_degraded_handling"]["ready"])

class TestPhase139QualityGate(unittest.TestCase):
    def test_pass(self): self.assertEqual(run_delivery_quality_gate()["phase139_delivery_quality_gate"]["overall"],"pass")
    def test_violations_0(self): self.assertEqual(run_delivery_quality_gate()["phase139_delivery_quality_gate"]["violations"],0)

class TestPhase139Guard(unittest.TestCase):
    def test_pass(self): self.assertEqual(run_cannot_conclude_guard()["phase139_cannot_conclude_guard"]["overall"],"pass")

class TestPhase139Backlog(unittest.TestCase):
    def test_deployed(self): self.assertIn("delivery",build_backlog_update()["phase139_backlog_update"]["phase139_status"])
    def test_next(self): self.assertIn("phase140",build_backlog_update()["phase139_backlog_update"]["next_phase"])

class TestPhase139Regression(unittest.TestCase):
    def test_phase138_regression(self):
        r=load_phase138_thesis()["phase139_phase138_thesis_loader"]
        self.assertEqual(r["theses_loaded"],8);self.assertTrue(r["all_research_only"])

if __name__=="__main__":
    unittest.main()
