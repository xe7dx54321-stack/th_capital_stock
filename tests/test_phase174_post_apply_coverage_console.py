import unittest, json, sys, os
sys.path.insert(0,"08_scripts/lib")
sys.path.insert(0,"08_scripts/reporting")
sys.path.insert(0,"08_scripts/jobs")

class TestPhase174Config(unittest.TestCase):
    def test_config(self):
        from smr_phase174_config import load_phase174_config
        c = load_phase174_config()
        self.assertEqual(c["phase174_config"]["status"],"loaded")
        self.assertEqual(c["phase174_config"]["candidates_count"],13)
        self.assertTrue(c["phase174_config"]["research_only"])

class TestPhase174Registry(unittest.TestCase):
    def test_registry_loads(self):
        from smr_phase174_coverage_state_registry import build_coverage_state_registry
        r = build_coverage_state_registry()
        reg = r["phase174_coverage_state_registry"]
        self.assertEqual(reg["status"],"state_loaded")
        self.assertEqual(reg["coverage_state_count"],13)
        self.assertEqual(reg["activated_count"],9)
        self.assertEqual(reg["kept_count"],2)
        self.assertEqual(reg["deferred_count"],1)
        self.assertEqual(reg["rejected_count"],1)
        self.assertTrue(reg["coverage_state_only"])

    def test_registry_no_input(self):
        from smr_phase174_coverage_state_registry import load_owner_decision_input
        self.assertIsNotNone(load_owner_decision_input())

class TestPhase174Loader(unittest.TestCase):
    def test_loader_counts(self):
        from smr_phase174_coverage_state_loader import load_coverage_state
        s = load_coverage_state()
        sl = s["phase174_coverage_state_loader"]
        self.assertTrue(sl["state_loaded"])
        self.assertEqual(sl["coverage_state_count"],13)
        self.assertEqual(sl["activated_count"],9)
        self.assertEqual(sl["kept_count"],2)

class TestPhase174Cards(unittest.TestCase):
    def test_cards_count(self):
        from smr_phase174_coverage_cards import build_coverage_cards
        c = build_coverage_cards()
        self.assertEqual(c["phase174_coverage_cards"]["cards_count"],13)

    def test_activate_cards_monitoring(self):
        from smr_phase174_coverage_cards import build_coverage_cards
        c = build_coverage_cards()
        active = [x for x in c["phase174_coverage_cards"]["cards"] if x["daily_monitoring_eligible"]]
        self.assertEqual(len(active),9)

class TestPhase174DailyPlan(unittest.TestCase):
    def test_daily_plan(self):
        from smr_phase174_daily_monitoring_plan import build_daily_monitoring_plan
        d = build_daily_monitoring_plan()
        self.assertEqual(d["phase174_daily_monitoring_plan"]["eligible_candidates"],9)
        self.assertTrue(d["phase174_daily_monitoring_plan"]["monitoring_not_trade"])

class TestPhase174WeeklyPlan(unittest.TestCase):
    def test_weekly_plan(self):
        from smr_phase174_weekly_review_plan import build_weekly_review_plan
        w = build_weekly_review_plan()
        self.assertEqual(w["phase174_weekly_review_plan"]["eligible_candidates"],11)

class TestPhase174AgentTasks(unittest.TestCase):
    def test_task_queue(self):
        from smr_phase174_agent_task_queue import build_agent_task_queue
        t = build_agent_task_queue()
        self.assertTrue(t["phase174_agent_task_queue"]["no_trade_tasks"])
        self.assertTrue(t["phase174_agent_task_queue"]["total_tasks"]>0)

    def test_no_trade_terms_in_tasks(self):
        from smr_phase174_agent_task_queue import build_agent_task_queue
        t = build_agent_task_queue()
        t_raw = json.dumps(t, ensure_ascii=False)
        tasks_only = json.dumps([x["tasks"] for x in t["phase174_agent_task_queue"]["tasks"]], ensure_ascii=False).lower()
        for term in ["buy "," sell "," hold "," short "]:
            self.assertNotIn(term, tasks_only)

class TestPhase174History(unittest.TestCase):
    def test_history(self):
        from smr_phase174_coverage_state_history import build_coverage_state_history
        h = build_coverage_state_history()
        self.assertTrue(h["phase174_coverage_state_history"]["history_path_ignored"])

class TestPhase174Adjustment(unittest.TestCase):
    def test_adjustment_workflow(self):
        from smr_phase174_manual_adjustment import build_manual_adjustment_workflow
        a = build_manual_adjustment_workflow()
        self.assertEqual(a["phase174_manual_adjustment_workflow"]["candidates_with_workflow"],13)
        self.assertTrue(a["phase174_manual_adjustment_workflow"]["manual_adjustment_not_auto_apply"])

class TestPhase174Drift(unittest.TestCase):
    def test_drift_no_false_positive(self):
        from smr_phase174_coverage_drift_checker import build_coverage_drift_checker
        d = build_coverage_drift_checker()
        self.assertEqual(d["phase174_coverage_drift_checker"]["drift_detected"],0)

class TestPhase174Debt(unittest.TestCase):
    def test_debt_recorded(self):
        from smr_phase174_trade_term_debt import build_trade_term_debt_recorder
        d = build_trade_term_debt_recorder()
        self.assertTrue(d["phase174_trade_term_debt"]["debt_recorded"])
        self.assertIn("substring",d["phase174_trade_term_debt"]["known_issue"])

class TestPhase174Guard(unittest.TestCase):
    def test_guard(self):
        from smr_phase174_guard import build_phase174_guard
        g = build_phase174_guard()
        self.assertEqual(g["phase174_guard"]["status"],"pass")

    def test_quality_gate(self):
        from smr_phase174_guard import build_phase174_quality_gate
        q = build_phase174_quality_gate()
        self.assertEqual(q["phase174_quality_gate"]["status"],"pass")
        self.assertEqual(q["phase174_quality_gate"]["violations"],0)

    def test_cc(self):
        from smr_phase174_guard import build_phase174_cannot_conclude_guard
        c = build_phase174_cannot_conclude_guard()
        self.assertEqual(c["phase174_cannot_conclude_guard"]["status"],"pass")
        self.assertEqual(c["phase174_cannot_conclude_guard"]["violations"],0)

class TestPhase174Console(unittest.TestCase):
    def test_console(self):
        from build_phase174_post_apply_console import build_post_apply_console
        c = build_post_apply_console()
        co = c["phase174_post_apply_console"]
        self.assertEqual(co["coverage_state_count"],13)
        self.assertEqual(co["activated_count"],9)

class TestPhase174Board(unittest.TestCase):
    def test_board(self):
        from build_phase174_post_apply_board import build_post_apply_board
        b = build_post_apply_board()
        self.assertEqual(b["phase174_post_apply_board"]["tickers_total"],13)

class TestPhase174Brief(unittest.TestCase):
    def test_brief(self):
        from build_phase174_post_apply_brief import build_post_apply_brief
        b = build_post_apply_brief()
        s = b["phase174_post_apply_brief"]["sections"]
        self.assertEqual(s["boss_summary"]["total_candidates"],13)

    def test_brief_no_trade_advice(self):
        from build_phase174_post_apply_brief import build_post_apply_brief
        b = build_post_apply_brief()
        rb = b["phase174_post_apply_brief"]["sections"]["research_boundary"]
        self.assertTrue(rb["no_trade_recommendation"])
        self.assertTrue(rb["no_target_price"])
        self.assertTrue(rb["no_position_sizing"])
        self.assertTrue(rb["no_broker_api"])

class TestPhase174Dashboard(unittest.TestCase):
    def test_dashboard(self):
        from build_phase174_dashboard import build_dashboard
        d = build_dashboard()
        self.assertEqual(d["phase174_dashboard"]["summary"]["coverage_state_count"],13)
        self.assertEqual(d["phase174_dashboard"]["summary"]["trade_recommendation_created"],0)
        self.assertEqual(d["phase174_dashboard"]["summary"]["target_price_created"],0)

class TestPhase174Pipeline(unittest.TestCase):
    def test_dry_run(self):
        from run_phase174_post_apply_coverage_console import run_pipeline
        r = run_pipeline("dry-run")
        self.assertEqual(r["phase174_post_apply_coverage_console_pipeline"]["mode"],"dry-run")
        self.assertEqual(r["phase174_post_apply_coverage_console_pipeline"]["guard"],"pass")

    def test_execute(self):
        from run_phase174_post_apply_coverage_console import run_pipeline
        r = run_pipeline("execute")
        self.assertEqual(r["phase174_post_apply_coverage_console_pipeline"]["mode"],"execute")
        self.assertTrue(r["phase174_post_apply_coverage_console_pipeline"]["state_written_to_generated"])

    def test_skip_network(self):
        from run_phase174_post_apply_coverage_console import run_pipeline
        r = run_pipeline("skip-network")
        self.assertEqual(r["phase174_post_apply_coverage_console_pipeline"]["mode"],"skip-network")

if __name__=="__main__":
    unittest.main()
