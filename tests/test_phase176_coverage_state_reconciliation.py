import unittest, json, sys, os
sys.path.insert(0,"08_scripts/lib"); sys.path.insert(0,"08_scripts/reporting"); sys.path.insert(0,"08_scripts/jobs")

class TestPhase176Loaders(unittest.TestCase):
    def test_phase172_state(self):
        from smr_phase176_reconciliation import load_phase172_state
        s = load_phase172_state()
        self.assertTrue(s["phase172_state"]["loaded"])
        self.assertEqual(s["phase172_state"]["coverage_state_count"],13)
        self.assertEqual(s["phase172_state"]["activated_count"],9)

    def test_phase174_artifacts(self):
        from smr_phase176_reconciliation import load_phase174_artifacts
        s = load_phase174_artifacts()
        self.assertTrue(s["phase174_artifacts"]["loaded"])
        self.assertEqual(s["phase174_artifacts"]["coverage_cards_count"],13)

    def test_phase175_artifacts(self):
        from smr_phase176_reconciliation import load_phase175_artifacts
        s = load_phase175_artifacts()
        self.assertTrue(s["phase175_artifacts"]["loaded"])
        self.assertEqual(s["phase175_artifacts"]["task_count"],41)

class TestPhase176Reconciler(unittest.TestCase):
    def test_universe(self):
        from smr_phase176_reconciliation import build_universe_reconciler
        u = build_universe_reconciler()
        self.assertTrue(u["phase176_universe_reconciler"]["candidates_total"] >= 12)

    def test_mismatch_analyzer(self):
        from smr_phase176_reconciliation import build_candidate_mismatch_analyzer
        m = build_candidate_mismatch_analyzer()
        mm = m["phase176_candidate_mismatch_analyzer"]
        self.assertEqual(mm["coverage_state_count"],13)
        self.assertEqual(mm["task_candidate_count"],12)
        self.assertEqual(mm["mismatch_status"],"explained")

    def test_task_matrix(self):
        from smr_phase176_reconciliation import build_task_coverage_matrix
        t = build_task_coverage_matrix()
        self.assertEqual(t["phase176_task_coverage_matrix"]["orphan_task_count"],0)
        self.assertEqual(t["phase176_task_coverage_matrix"]["duplicate_task_count"],0)

    def test_artifact_completeness(self):
        from smr_phase176_reconciliation import build_artifact_completeness_checker
        a = build_artifact_completeness_checker()
        self.assertIn(a["phase176_artifact_completeness"]["status"],["pass","partial"])

    def test_history_integrity(self):
        from smr_phase176_reconciliation import build_history_integrity_checker
        h = build_history_integrity_checker()
        self.assertIn(h["phase176_history_integrity"]["status"],["pass","partial"])

    def test_monitoring_consistency(self):
        from smr_phase176_reconciliation import build_monitoring_plan_consistency_checker
        m = build_monitoring_plan_consistency_checker()
        self.assertTrue(m["phase176_monitoring_plan_consistency"]["daily_consistent"])

    def test_treatment_validator(self):
        from smr_phase176_reconciliation import build_rejected_deferred_treatment_validator
        t = build_rejected_deferred_treatment_validator()
        self.assertTrue(t["phase176_rejected_deferred_treatment"]["treatment_valid"])

    def test_repair_plan(self):
        from smr_phase176_reconciliation import build_repair_plan
        r = build_repair_plan()
        self.assertFalse(r["phase176_repair_plan"]["repair_required"])

class TestPhase176Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase176_reconciliation import build_phase176_guard
        g = build_phase176_guard()
        self.assertEqual(g["phase176_guard"]["status"],"pass")
        self.assertFalse(g["phase176_guard"]["state_write_allowed"])

    def test_quality_gate(self):
        from smr_phase176_reconciliation import build_phase176_quality_gate
        q = build_phase176_quality_gate()
        self.assertEqual(q["phase176_quality_gate"]["status"],"pass")
        self.assertEqual(q["phase176_quality_gate"]["violations"],0)

    def test_cc(self):
        from smr_phase176_reconciliation import build_phase176_cannot_conclude_guard
        c = build_phase176_cannot_conclude_guard()
        self.assertEqual(c["phase176_cannot_conclude_guard"]["status"],"pass")

class TestPhase176Reporting(unittest.TestCase):
    def test_board(self):
        from build_phase176_reconciliation_board import build_reconciliation_board
        b = build_reconciliation_board()
        self.assertIn("coverage_state",b["phase176_reconciliation_board"])

    def test_dashboard(self):
        from build_phase176_reconciliation_board import build_dashboard
        d = build_dashboard()
        self.assertEqual(d["phase176_dashboard"]["summary"]["coverage_state_count"],13)

    def test_backlog(self):
        from build_phase176_reconciliation_board import build_backlog_update
        b = build_backlog_update()
        self.assertTrue(b["phase176_backlog_update"]["phase176_completed"])

class TestPhase176Pipeline(unittest.TestCase):
    def test_dry_run(self):
        from run_phase176_coverage_state_reconciliation import run_pipeline
        r = run_pipeline("dry-run")
        self.assertEqual(r["phase176_reconciliation_pipeline"]["mode"],"dry-run")
        self.assertEqual(r["phase176_reconciliation_pipeline"]["guard"],"pass")

    def test_execute(self):
        from run_phase176_coverage_state_reconciliation import run_pipeline
        r = run_pipeline("execute")
        self.assertEqual(r["phase176_reconciliation_pipeline"]["mode"],"execute")
        self.assertEqual(r["phase176_reconciliation_pipeline"]["candidate_mismatch_status"],"explained")

    def test_skip_network(self):
        from run_phase176_coverage_state_reconciliation import run_pipeline
        r = run_pipeline("skip-network")
        self.assertEqual(r["phase176_reconciliation_pipeline"]["mode"],"skip-network")

class TestPhase176Safety(unittest.TestCase):
    def test_no_state_write(self):
        from smr_phase176_reconciliation import build_phase176_guard
        g = build_phase176_guard()
        self.assertFalse(g["phase176_guard"]["state_write_allowed"])

    def test_output_has_safety_fields(self):
        from run_phase176_coverage_state_reconciliation import run_pipeline
        r = run_pipeline("execute")
        p = r["phase176_reconciliation_pipeline"]
        self.assertEqual(p["trade_recommendation_created"],0)
        self.assertEqual(p["target_price_created"],0)
        self.assertEqual(p["position_sizing_created"],0)
        self.assertFalse(p["broker_api_called"])
        self.assertFalse(p["state_write_allowed"])

if __name__=="__main__":
    unittest.main()
