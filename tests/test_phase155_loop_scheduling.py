import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase155Config(unittest.TestCase):
    def test_config(self):
        from smr_phase155_config import load_phase155_config
        c = load_phase155_config()
        self.assertEqual(c["phase"], "phase155")
        self.assertTrue(c["research_only"])
        self.assertTrue(c["agent_loop_scheduling_enabled"])
        self.assertFalse(c["system_scheduler_registration_allowed"])
        self.assertFalse(c["live_llm_call_allowed"])
        self.assertFalse(c["activation_allowed"])

class TestPhase155Plans(unittest.TestCase):
    def setUp(self):
        self.targets = {"core":["NVDA","AVGO"],"watch":["300308.SZ","300394.SZ"],"candidate":["TSM"],"ready":["MRVL"],"all":["NVDA","AVGO","300308.SZ","300394.SZ","TSM","MRVL"]}

    def test_daily_plan(self):
        from smr_phase155_daily_loop_plan import build_daily_loop_plan
        r = build_daily_loop_plan(self.targets)
        self.assertTrue(r["phase155_daily_loop_plan"]["schedule_is_not_trade_plan"])

    def test_weekly_plan(self):
        from smr_phase155_weekly_loop_plan import build_weekly_loop_plan
        r = build_weekly_loop_plan(self.targets)
        self.assertEqual(r["phase155_weekly_loop_plan"]["weekly_targets_total"], 6)

    def test_event_plan(self):
        from smr_phase155_event_trigger_plan import build_event_trigger_plan
        r = build_event_trigger_plan()
        self.assertTrue(r["phase155_event_trigger_plan"]["event_trigger_is_not_trade_signal"])

    def test_tier_frequency(self):
        from smr_phase155_tier_frequency_policy import build_tier_frequency_policy
        r = build_tier_frequency_policy()
        self.assertTrue(r["phase155_tier_frequency_policy"]["tier_frequency_not_investment_rating"])

    def test_history_reader_first_run(self):
        from smr_phase155_history_reader import read_loop_run_history
        r = read_loop_run_history()
        self.assertTrue(r["phase155_history_reader"]["is_first_run"])

    def test_delta_first_run(self):
        from smr_phase155_delta_comparator import build_loop_delta_comparator
        r = build_loop_delta_comparator(None, {"targets":self.targets["all"]})
        self.assertFalse(r["phase155_delta_comparator"]["delta_available"])

    def test_owner_digest_no_trade(self):
        from smr_phase155_owner_digest import build_owner_review_digest
        r = build_owner_review_digest(self.targets["all"])
        self.assertTrue(r["phase155_owner_digest"]["no_trade_actions"])

class TestPhase155Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase155_loop_scheduling_pipeline import run
        r = run("dry-run")
        p = r["phase155_loop_scheduling_pipeline"]
        self.assertGreater(p["weekly_targets"], 0)
        self.assertEqual(p["quality_gate"], "pass")
        self.assertEqual(p["guard"], "pass")
        self.assertEqual(p["violations"], 0)
        self.assertTrue(p["schedule_not_trade_plan"])
        self.assertTrue(p["event_not_trade_signal"])
        self.assertTrue(p["history_not_pnl"])
        self.assertTrue(p["digest_not_advice"])
        self.assertFalse(p["watch_core_updated"])
        self.assertEqual(p["mock_used"], False)

if __name__ == "__main__":
    unittest.main()
