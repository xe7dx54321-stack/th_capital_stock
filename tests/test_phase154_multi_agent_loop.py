import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase154Config(unittest.TestCase):
    def test_config(self):
        from smr_phase154_config import load_phase154_config
        c = load_phase154_config()
        self.assertEqual(c["phase"], "phase154")
        self.assertTrue(c["research_only"])
        self.assertTrue(c["multi_agent_research_loop_enabled"])
        self.assertFalse(c["live_llm_call_allowed"])
        self.assertFalse(c["activation_allowed"])
        self.assertFalse(c["auto_add_to_watchlist_allowed"])

class TestPhase154Agents(unittest.TestCase):
    def setUp(self):
        self.targets = ["NVDA", "AVGO", "300394.SZ"]

    def test_opportunity_agent(self):
        from smr_phase154_opportunity_agent import run_opportunity_agent
        r = run_opportunity_agent(self.targets)
        self.assertEqual(r["phase154_opportunity_agent"]["targets_scanned"], 3)
        self.assertTrue(r["phase154_opportunity_agent"]["agent_simulation_only"])

    def test_evidence_agent(self):
        from smr_phase154_evidence_agent import run_evidence_agent
        r = run_evidence_agent(self.targets, {})
        self.assertEqual(r["phase154_evidence_agent"]["targets_checked"], 3)
        self.assertFalse(r["phase154_evidence_agent"]["live_llm_call_made"])

    def test_risk_agent(self):
        from smr_phase154_risk_agent import run_risk_agent
        r = run_risk_agent(self.targets, {})
        self.assertEqual(r["phase154_risk_agent"]["targets_screened"], 3)
        blocked = [x for x in r["phase154_risk_agent"]["results"] if x["blocked"]]
        self.assertEqual(len(blocked), 1)

    def test_thesis_agent(self):
        from smr_phase154_thesis_agent import run_thesis_agent
        r = run_thesis_agent(self.targets, {})
        self.assertFalse(r["phase154_thesis_agent"]["confirmed_thesis_created"])

    def test_judge_agent(self):
        from smr_phase154_judge_agent_loop import run_judge_agent_loop
        r = run_judge_agent_loop(self.targets, [])
        j = r["phase154_judge_agent_loop"]
        self.assertEqual(j["passed"], 2)
        self.assertEqual(j["blocked"], 1)
        self.assertTrue(j["results"][0]["judge_pass_not_equal_to_investment_approval"])

    def test_owner_actions_no_trade(self):
        from smr_phase154_owner_action_proposal import build_owner_action_proposal
        r = build_owner_action_proposal(self.targets)
        self.assertTrue(r["phase154_owner_action_proposal"]["no_trade_actions"])
        for a in r["phase154_owner_action_proposal"]["actions"]:
            self.assertFalse(a["contains_trade_action"])

class TestPhase154Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase154_multi_agent_loop_pipeline import run
        r = run("dry-run")
        p = r["phase154_multi_agent_loop_pipeline"]
        self.assertGreater(p["loop_targets_total"], 0)
        self.assertEqual(p["quality_gate"], "pass")
        self.assertEqual(p["guard"], "pass")
        self.assertEqual(p["violations"], 0)
        self.assertTrue(p["research_only"])
        self.assertTrue(p["agent_simulation_only"])
        self.assertFalse(p["live_llm_call_made"])
        self.assertFalse(p["confirmed_thesis_created"])
        self.assertFalse(p["owner_actions_contain_trade"])
        self.assertEqual(p["mock_used"], False)
        self.assertEqual(p["trade_recommendation_created"], 0)

if __name__ == "__main__":
    unittest.main()
