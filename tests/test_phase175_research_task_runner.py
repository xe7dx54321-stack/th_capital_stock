import unittest, json, sys, os
sys.path.insert(0,"08_scripts/lib"); sys.path.insert(0,"08_scripts/reporting"); sys.path.insert(0,"08_scripts/jobs")

class TestPhase175Config(unittest.TestCase):
    def test_config(self):
        from smr_phase175_config import load_phase175_config
        c = load_phase175_config()
        self.assertEqual(c["phase175_config"]["status"],"loaded")
        self.assertTrue(c["phase175_config"]["research_only"])

class TestPhase175TaskLoader(unittest.TestCase):
    def test_task_count(self):
        from smr_phase175_task_queue_loader import load_task_queue
        q = load_task_queue()
        self.assertTrue(q["phase175_task_queue_loader"]["task_queue_loaded"])
        self.assertEqual(q["phase175_task_queue_loader"]["task_count"],41)

    def test_candidate_agent_count(self):
        from smr_phase175_task_queue_loader import load_task_queue
        q = load_task_queue()
        self.assertEqual(q["phase175_task_queue_loader"]["candidate_count"],12)
        self.assertEqual(q["phase175_task_queue_loader"]["agent_count"],7)

class TestPhase175BatchPlanner(unittest.TestCase):
    def test_eligibility(self):
        from smr_phase175_task_batch_planner import check_task_eligibility
        e = check_task_eligibility("execute")
        self.assertEqual(e["phase175_task_eligibility"]["eligible_count"],41)

    def test_skip_network_defers(self):
        from smr_phase175_task_batch_planner import check_task_eligibility
        e = check_task_eligibility("skip-network")
        self.assertTrue(e["phase175_task_eligibility"]["deferred_count"] >= 0)

    def test_batch_plan(self):
        from smr_phase175_task_batch_planner import build_batch_plan
        bp = build_batch_plan("execute")
        self.assertTrue(bp["phase175_task_batch_planner"]["batch_count"] > 0)

class TestPhase175Executor(unittest.TestCase):
    def test_dry_run(self):
        from smr_phase175_task_executor import run_all_tasks
        r = run_all_tasks("dry-run")
        ex = r["phase175_task_executor"]
        self.assertEqual(ex["total_tasks"],41)
        self.assertTrue(ex["research_only"])

    def test_execute_mode(self):
        from smr_phase175_task_executor import run_all_tasks
        r = run_all_tasks("execute")
        ex = r["phase175_task_executor"]
        self.assertEqual(ex["total_tasks"],41)
        self.assertTrue(ex["completed"] > 0)

    def test_skip_network_mode(self):
        from smr_phase175_task_executor import run_all_tasks
        r = run_all_tasks("skip-network")
        ex = r["phase175_task_executor"]
        self.assertEqual(ex["total_tasks"],41)

    def test_agent_executors_exist(self):
        from smr_phase175_task_executor import AGENT_EXECUTORS
        self.assertEqual(len(AGENT_EXECUTORS),7)
        for agent in ["quant_monitor","research_analyst","evidence_collector","drift_monitor","event_monitor","thesis_validator","source_auditor"]:
            self.assertIn(agent,AGENT_EXECUTORS)

class TestPhase175Artifacts(unittest.TestCase):
    def test_artifacts_write(self):
        from smr_phase175_task_executor import run_all_tasks, write_task_artifacts
        r = run_all_tasks("execute")
        a = write_task_artifacts(r,"execute")
        self.assertTrue(a["artifacts_written"])
        self.assertTrue(a["path_ignored"])

    def test_history_write(self):
        from smr_phase175_task_executor import run_all_tasks, write_task_history
        r = run_all_tasks("execute")
        h = write_task_history(r,"execute")
        self.assertTrue(h["history_written"])
        self.assertTrue(h["path_ignored"])

class TestPhase175Guard(unittest.TestCase):
    def test_guard(self):
        from smr_phase175_guard import build_phase175_guard
        g = build_phase175_guard()
        self.assertEqual(g["phase175_guard"]["status"],"pass")

    def test_quality_gate(self):
        from smr_phase175_guard import build_phase175_quality_gate
        q = build_phase175_quality_gate()
        self.assertEqual(q["phase175_quality_gate"]["status"],"pass")
        self.assertEqual(q["phase175_quality_gate"]["violations"],0)

    def test_cc(self):
        from smr_phase175_guard import build_phase175_cannot_conclude_guard
        c = build_phase175_cannot_conclude_guard()
        self.assertEqual(c["phase175_cannot_conclude_guard"]["status"],"pass")

    def test_retry_planner(self):
        from smr_phase175_guard import build_retry_planner
        r = build_retry_planner("execute")
        self.assertIn("retry_plan",r["phase175_retry_planner"])

    def test_degraded_handler_structure(self):
        from smr_phase175_guard import build_degraded_handler
        d = build_degraded_handler("execute")
        self.assertIn("deferred_count",d["phase175_degraded_handler"])
        self.assertTrue(d["phase175_degraded_handler"]["degraded_not_failed"])

class TestPhase175Reporting(unittest.TestCase):
    def test_task_reports(self):
        from build_phase175_task_reports import (build_task_queue_loader_report,
            build_task_batch_plan_report, build_task_execution_report, build_agent_execution_report)
        q = build_task_queue_loader_report()
        self.assertTrue(q["phase175_task_queue_loader_report"]["task_queue_loaded"])
        bp = build_task_batch_plan_report("execute")
        self.assertTrue(bp["phase175_task_batch_plan_report"]["batch_count"] > 0)
        ex = build_task_execution_report("execute")
        self.assertTrue(ex["phase175_task_execution_report"]["completed"] > 0)
        ag = build_agent_execution_report("execute")
        self.assertEqual(ag["phase175_agent_execution_report"]["agent_count"],7)

    def test_digest(self):
        from build_phase175_daily_task_digest import build_daily_task_digest
        d = build_daily_task_digest("execute")
        self.assertIn("summary",d["phase175_daily_task_digest"])

    def test_console_integration(self):
        from build_phase175_console_integration_report import build_console_integration
        c = build_console_integration("execute")
        self.assertTrue(c["phase175_console_integration"]["phase175_integrated"])

    def test_dashboard(self):
        from build_phase175_dashboard import build_dashboard
        d = build_dashboard("execute")
        self.assertEqual(d["phase175_dashboard"]["summary"]["task_count"],41)

class TestPhase175Pipeline(unittest.TestCase):
    def test_dry_run(self):
        from run_phase175_research_task_runner import run_pipeline
        r = run_pipeline("dry-run")
        self.assertEqual(r["phase175_research_task_runner_pipeline"]["mode"],"dry-run")
        self.assertEqual(r["phase175_research_task_runner_pipeline"]["guard"],"pass")

    def test_execute(self):
        from run_phase175_research_task_runner import run_pipeline
        r = run_pipeline("execute")
        self.assertEqual(r["phase175_research_task_runner_pipeline"]["mode"],"execute")
        self.assertTrue(r["phase175_research_task_runner_pipeline"]["artifacts_written"])

    def test_skip_network(self):
        from run_phase175_research_task_runner import run_pipeline
        r = run_pipeline("skip-network")
        self.assertEqual(r["phase175_research_task_runner_pipeline"]["mode"],"skip-network")

class TestPhase175Safety(unittest.TestCase):
    def test_no_trade_terms(self):
        from smr_phase175_task_executor import run_all_tasks
        r = run_all_tasks("execute")
        tasks_str = json.dumps(r, ensure_ascii=False).lower()
        for term in ["buy "," sell "," hold ","trade_order","target_price","position_size"]:
            self.assertNotIn(term, tasks_str)

    def test_execution_is_research_only(self):
        from smr_phase175_task_executor import run_all_tasks
        r = run_all_tasks("execute")
        self.assertTrue(r["phase175_task_executor"]["research_only"])
        self.assertTrue(r["phase175_task_executor"]["no_trade_executed"])

if __name__=="__main__":
    unittest.main()
