import unittest, json, sys, os
sys.path.insert(0,"08_scripts/lib"); sys.path.insert(0,"08_scripts/reporting"); sys.path.insert(0,"08_scripts/jobs")

class TestPhase179Validator(unittest.TestCase):
    def test_no_input(self):
        from smr_phase179_review_processing import build_input_schema_validator
        v = build_input_schema_validator()
        self.assertEqual(v["phase179_schema_validator"]["status"],"no_input")
        self.assertEqual(v["phase179_schema_validator"]["input_records_loaded"],0)

    def test_manifest_structure(self):
        from smr_phase179_review_processing import build_input_schema_validator
        v = build_input_schema_validator()
        self.assertIn("manifest",v["phase179_schema_validator"])

class TestPhase179Classifier(unittest.TestCase):
    def test_no_input_classifier(self):
        from smr_phase179_review_processing import build_review_status_classifier
        c = build_review_status_classifier()
        self.assertEqual(c["phase179_review_classifier"]["review_input_state"],"no_owner_review_input_pending")
        self.assertEqual(c["phase179_review_classifier"]["pending"],9)

class TestPhase179Revision(unittest.TestCase):
    def test_revision_preview(self):
        from smr_phase179_review_processing import build_revision_task_preview
        r = build_revision_task_preview()
        self.assertEqual(r["phase179_revision_task_preview"]["revision_task_count"],0)
        self.assertTrue(r["phase179_revision_task_preview"]["auto_execution_disabled"])

class TestPhase179Eligibility(unittest.TestCase):
    def test_daily_eligibility(self):
        from smr_phase179_review_processing import build_daily_brief_eligibility
        d = build_daily_brief_eligibility()
        self.assertEqual(d["phase179_daily_brief_eligibility"]["eligible_count"],0)
        self.assertTrue(d["phase179_daily_brief_eligibility"]["not_trade_signal"])

    def test_weekly_eligibility(self):
        from smr_phase179_review_processing import build_weekly_review_eligibility
        w = build_weekly_review_eligibility()
        self.assertEqual(w["phase179_weekly_review_eligibility"]["eligible_count"],0)

class TestPhase179Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase179_review_processing import build_phase179_guard
        g = build_phase179_guard()
        self.assertEqual(g["phase179_guard"]["status"],"pass")
        self.assertTrue(g["phase179_guard"]["review_input_read_only"])

    def test_quality_gate(self):
        from smr_phase179_review_processing import build_phase179_quality_gate
        q = build_phase179_quality_gate()
        self.assertEqual(q["phase179_quality_gate"]["status"],"pass")
        self.assertEqual(q["phase179_quality_gate"]["violations"],0)

    def test_cc(self):
        from smr_phase179_review_processing import build_phase179_cannot_conclude_guard
        c = build_phase179_cannot_conclude_guard()
        self.assertEqual(c["phase179_cannot_conclude_guard"]["status"],"pass")

class TestPhase179Reporting(unittest.TestCase):
    def test_board(self):
        from build_phase179_review_processing_board import build_review_processing_board
        b = build_review_processing_board()
        self.assertIn("validator",b["phase179_review_processing_board"])

    def test_dashboard(self):
        from build_phase179_review_processing_board import build_dashboard
        d = build_dashboard()
        self.assertEqual(d["phase179_dashboard"]["summary"]["packet_count"],9)

class TestPhase179Pipeline(unittest.TestCase):
    def test_dry_run(self):
        from run_phase179_owner_review_input_processing import run_pipeline
        r = run_pipeline("dry-run")
        self.assertEqual(r["phase179_review_processing_pipeline"]["mode"],"dry-run")
        self.assertEqual(r["phase179_review_processing_pipeline"]["guard"],"pass")

    def test_execute(self):
        from run_phase179_owner_review_input_processing import run_pipeline
        r = run_pipeline("execute")
        self.assertEqual(r["phase179_review_processing_pipeline"]["packet_count"],9)
        self.assertFalse(r["phase179_review_processing_pipeline"]["auto_signoff"])

    def test_skip_network(self):
        from run_phase179_owner_review_input_processing import run_pipeline
        r = run_pipeline("skip-network")
        self.assertEqual(r["phase179_review_processing_pipeline"]["mode"],"skip-network")

if __name__=="__main__":
    unittest.main()
