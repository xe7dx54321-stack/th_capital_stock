import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "reporting"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "jobs"))

class TestPhase165Config(unittest.TestCase):
    def test_config(self):
        from smr_phase165_config import load_phase165_config
        c = load_phase165_config()
        self.assertEqual(c["phase"], "phase165")
        self.assertTrue(c["agent_simulation_only"])
        self.assertFalse(c["llm_api_enabled"])
        self.assertFalse(c["activation_execution_allowed"])

class TestPhase165Domain(unittest.TestCase):
    def test_registry(self):
        from smr_phase165_domain_registry import build_phase165_domain_registry
        r = build_phase165_domain_registry()
        self.assertEqual(len(r["phase165_domain_registry"]["domains"]), 3)

class TestPhase165Readiness(unittest.TestCase):
    def test_analyzer(self):
        from smr_phase165_readiness import analyze_not_ready_reasons
        r = analyze_not_ready_reasons()
        a = r["phase165_not_ready_analyzer"]
        self.assertEqual(a["not_ready_analyzed_count"], 13)
        self.assertIn("network_data_required", a["primary_blockers"])

    def test_taxonomy(self):
        from smr_phase165_readiness import build_blocker_taxonomy
        r = build_blocker_taxonomy()
        self.assertEqual(len(r["phase165_blocker_taxonomy"]["taxonomy"]), 4)

    def test_repair(self):
        from smr_phase165_readiness import analyze_not_ready_reasons, build_repair_planner
        analysis = analyze_not_ready_reasons()
        r = build_repair_planner(analysis)
        self.assertEqual(r["phase165_repair_planner"]["total_candidates"], 13)

class TestPhase165Planners(unittest.TestCase):
    def test_evidence(self):
        from smr_phase165_planners import build_evidence_gap_planner
        r = build_evidence_gap_planner()
        self.assertEqual(r["phase165_evidence_gap_planner"]["total"], 13)

    def test_source(self):
        from smr_phase165_planners import build_source_repair_planner
        r = build_source_repair_planner()
        self.assertTrue(r["phase165_source_repair_planner"]["all_sources_available"])

    def test_thesis(self):
        from smr_phase165_planners import build_thesis_seed_refiner
        r = build_thesis_seed_refiner()
        self.assertEqual(r["phase165_thesis_seed_refiner"]["total"], 13)
        self.assertTrue(r["phase165_thesis_seed_refiner"]["thesis_seed_not_confirmed"])

    def test_risk(self):
        from smr_phase165_planners import build_risk_review_planner
        r = build_risk_review_planner()
        self.assertTrue(r["phase165_risk_review_planner"]["risk_review_not_investment_rating"])

class TestPhase165Agents(unittest.TestCase):
    def test_all_agents(self):
        from smr_phase165_agents import (run_opportunity_agent, run_evidence_agent, run_risk_agent, run_thesis_agent, run_deepdive_agent, run_brief_agent, run_judge_agent)
        agents = [run_opportunity_agent, run_evidence_agent, run_risk_agent, run_thesis_agent, run_deepdive_agent, run_brief_agent, run_judge_agent]
        for fn in agents:
            r = fn()
            k = list(r.keys())[0]
            self.assertEqual(r[k]["passes"], 13)
            self.assertTrue(r[k]["agent_simulation_only"])
            self.assertFalse(r[k]["llm_api_called"])

    def test_judge_blocks_trade(self):
        from smr_phase165_agents import run_judge_agent
        r = run_judge_agent()
        j = r["phase165_judge_agent"]
        self.assertTrue(j["trade_language_blocked"])
        self.assertEqual(j["trade_terms_found"], 0)

    def test_handoff(self):
        from smr_phase165_agents import build_handoff_map
        r = build_handoff_map()
        self.assertEqual(len(r["phase165_handoff_map"]["agents"]), 7)

class TestPhase165Packets(unittest.TestCase):
    def setUp(self):
        from smr_phase165_readiness import analyze_not_ready_reasons, build_repair_planner
        from smr_phase165_agents import (run_opportunity_agent, run_evidence_agent, run_risk_agent, run_thesis_agent, run_deepdive_agent, run_brief_agent, run_judge_agent)
        self.readiness = analyze_not_ready_reasons()
        self.repair = build_repair_planner(self.readiness)
        self.opp = run_opportunity_agent(); self.ev = run_evidence_agent()
        self.rk = run_risk_agent(); self.th = run_thesis_agent()
        self.dd = run_deepdive_agent(); self.br = run_brief_agent(); self.ju = run_judge_agent()

    def test_packets(self):
        from smr_phase165_packets import build_research_packets
        r = build_research_packets(self.opp, self.ev, self.rk, self.th, self.dd, self.br, self.ju, self.repair, self.readiness)
        p = r["phase165_research_packets"]
        self.assertEqual(p["total"], 13)
        self.assertTrue(p["research_packets_not_thesis"])
        self.assertTrue(p["research_packets_not_advice"])

    def test_activation_preview(self):
        from smr_phase165_packets import build_activation_preview_conditions
        r = build_activation_preview_conditions()
        self.assertEqual(r["phase165_activation_preview"]["total"], 13)
        self.assertTrue(r["phase165_activation_preview"]["activation_preview_not_execution"])

    def test_owner_actions(self):
        from smr_phase165_packets import build_owner_next_actions
        r = build_owner_next_actions()
        self.assertTrue(r["phase165_owner_next_actions"]["no_buy_sell_hold"])

class TestPhase165Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase165_guard import build_readiness_guard
        self.assertEqual(build_readiness_guard()["phase165_readiness_guard"]["status"], "pass")
    def test_quality(self):
        from smr_phase165_quality_gate import build_quality_gate
        self.assertEqual(build_quality_gate()["phase165_quality_gate"]["status"], "pass")
    def test_cc(self):
        from smr_phase165_cannot_conclude_guard import build_cannot_conclude_guard
        cc = build_cannot_conclude_guard()
        self.assertEqual(cc["phase165_cannot_conclude_guard"]["status"], "pass")
        self.assertIn("300394 CNINFO org_id missing", cc["phase165_cannot_conclude_guard"]["reserved_constraints"])

class TestPhase165Pipeline(unittest.TestCase):
    def test_dry(self):
        from run_phase165_readiness_repair_pipeline import run
        r = run("dry-run")
        p = r["phase165_readiness_repair_pipeline"]
        self.assertEqual(p["not_ready_analyzed"], 13)
        self.assertEqual(p["research_packets"], 13)
        self.assertEqual(p["guard"], "pass")
        self.assertEqual(p["violations"], 0)
        self.assertTrue(p["agent_not_llm"])
        self.assertTrue(p["preview_not_execution"])
        self.assertTrue(p["owner_action_not_trade"])
    def test_execute(self):
        from run_phase165_readiness_repair_pipeline import run
        self.assertEqual(run("execute")["phase165_readiness_repair_pipeline"]["guard"], "pass")
    def test_skip(self):
        from run_phase165_readiness_repair_pipeline import run
        self.assertEqual(run("skip-network")["phase165_readiness_repair_pipeline"]["guard"], "pass")

if __name__=="__main__":
    unittest.main()
