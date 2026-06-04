import unittest, json, sys, os
sys.path.insert(0,"08_scripts/lib"); sys.path.insert(0,"08_scripts/reporting"); sys.path.insert(0,"08_scripts/jobs")

class TestPhase183DirtyItemSchema(unittest.TestCase):
    def test_schema_defined(self):
        from smr_phase183_dirty_intelligence_inbox import build_dirty_item_canonical_schema
        s = build_dirty_item_canonical_schema()
        ds = s["phase183_dirty_item_schema"]
        self.assertIn("item_id",ds["required_fields"])
        self.assertIn("ticker",ds["required_fields"])
        self.assertIn("source_url",ds["required_fields"])
        self.assertIn("source_category",ds["required_fields"])
        self.assertIn("buy_signal",ds["forbidden_fields"])
        self.assertIn("target_price",ds["forbidden_fields"])
        self.assertIn("needs_cleaning",ds["boolean_status_fields"])
        self.assertTrue(ds["research_only"])

class TestPhase183SimulatedInput(unittest.TestCase):
    def test_simulated_input(self):
        from smr_phase183_dirty_intelligence_inbox import build_simulated_input
        s = build_simulated_input()
        si = s["phase183_simulated_input"]
        self.assertTrue(si["simulated"])
        self.assertTrue(si["not_real_source"])
        self.assertFalse(si["clean_evidence_created"])
        self.assertEqual(si["item_count"],8)
        for item in si["items"]:
            self.assertIn("item_id",item)
            self.assertIn("ticker",item)
            self.assertIn("prompt_id",item)
            self.assertEqual(item["needs_cleaning"],True)
            self.assertEqual(item["clean_evidence_created"],False)
            self.assertEqual(item["packet_updated"],False)
            self.assertEqual(item["daily_brief_updated"],False)
            self.assertEqual(item["weekly_review_updated"],False)

class TestPhase183SchemaValidator(unittest.TestCase):
    def test_schema_validator(self):
        from smr_phase183_dirty_intelligence_inbox import build_schema_validator
        sv = build_schema_validator()
        v = sv["phase183_schema_validator"]
        self.assertGreater(v["items_checked"],0)
        self.assertEqual(v["valid_count"],v["items_checked"])
        self.assertEqual(v["invalid_count"],0)

class TestPhase183MetadataValidator(unittest.TestCase):
    def test_metadata_validator(self):
        from smr_phase183_dirty_intelligence_inbox import build_source_metadata_validator
        sm = build_source_metadata_validator()
        v = sm["phase183_source_metadata_validator"]
        self.assertGreater(v["items_checked"],0)
        self.assertEqual(v["valid_count"],v["items_checked"])

class TestPhase183Linker(unittest.TestCase):
    def test_linker(self):
        from smr_phase183_dirty_intelligence_inbox import build_ticker_prompt_source_linker
        l = build_ticker_prompt_source_linker()
        li = l["phase183_ticker_prompt_source_linker"]
        self.assertGreater(li["items_linked"],0)
        self.assertTrue(li["all_tickers_known"])

class TestPhase183Dedup(unittest.TestCase):
    def test_builder(self):
        from smr_phase183_dirty_intelligence_inbox import build_dedup_fingerprint_builder
        d = build_dedup_fingerprint_builder()
        self.assertGreater(d["phase183_dedup_fingerprint"]["items_processed"],0)

    def test_detector(self):
        from smr_phase183_dirty_intelligence_inbox import build_duplicate_detector
        d = build_duplicate_detector()
        self.assertEqual(d["phase183_duplicate_detector"]["duplicate_count"],0)

class TestPhase183Classifier(unittest.TestCase):
    def test_classifier(self):
        from smr_phase183_dirty_intelligence_inbox import build_item_classifier
        c = build_item_classifier()
        clf = c["phase183_item_classifier"]
        self.assertGreater(clf["items_classified"],0)
        self.assertGreater(clf["accepted_count"],0)
        self.assertEqual(clf["quarantined_count"],0)
        self.assertTrue(clf["stub_only"])
        for item in clf["classified"]:
            self.assertTrue(item["not_clean_evidence"])

class TestPhase183Quarantine(unittest.TestCase):
    def test_quarantine(self):
        from smr_phase183_dirty_intelligence_inbox import build_quarantine
        q = build_quarantine()
        self.assertTrue(q["phase183_quarantine"]["quarantine_not_deletion"])
        self.assertTrue(q["phase183_quarantine"]["quarantine_not_clean_evidence"])

class TestPhase183AcceptedManifest(unittest.TestCase):
    def test_manifest(self):
        from smr_phase183_dirty_intelligence_inbox import build_accepted_manifest
        m = build_accepted_manifest()
        am = m["phase183_accepted_manifest"]
        self.assertGreater(am["accepted_count"],0)
        self.assertTrue(am["manifest_is_dirty_not_clean"])
        self.assertTrue(am["accepted_does_not_mean_verified_evidence"])
        self.assertFalse(am["packet_updated_for_any"])
        self.assertFalse(am["daily_brief_updated_for_any"])

class TestPhase183Retention(unittest.TestCase):
    def test_retention_policy(self):
        from smr_phase183_dirty_intelligence_inbox import build_retention_policy
        r = build_retention_policy()
        self.assertFalse(r["phase183_retention_policy"]["full_raw_save_allowed"])
        self.assertFalse(r["phase183_retention_policy"]["raw_full_text_save_allowed"])

    def test_copyright_policy(self):
        from smr_phase183_dirty_intelligence_inbox import build_copyright_raw_save_policy
        c = build_copyright_raw_save_policy()
        self.assertTrue(c["phase183_copyright_policy"]["raw_full_text_save_disabled"])
        self.assertTrue(c["phase183_copyright_policy"]["snippet_only_allowed"])

class TestPhase183Audit(unittest.TestCase):
    def test_audit_log(self):
        from smr_phase183_dirty_intelligence_inbox import build_audit_log
        a = build_audit_log()
        self.assertGreater(a["phase183_audit_log"]["audit_events"],0)

class TestPhase183DirtyToClean(unittest.TestCase):
    def test_interface_placeholder(self):
        from smr_phase183_dirty_intelligence_inbox import build_dirty_to_clean_interface_placeholder
        d = build_dirty_to_clean_interface_placeholder()
        self.assertTrue(d["phase183_dirty_to_clean_interface"]["output_not_yet_built"])
        self.assertTrue(d["phase183_dirty_to_clean_interface"]["auto_clean_disabled"])

class TestPhase183NoInput(unittest.TestCase):
    def test_no_input_mode(self):
        from smr_phase183_dirty_intelligence_inbox import build_no_input_mode
        n = build_no_input_mode()
        self.assertFalse(n["phase183_no_input_mode"]["dirty_input_present"])
        self.assertEqual(n["phase183_no_input_mode"]["quality_gate"],"pass")
        self.assertEqual(n["phase183_no_input_mode"]["accepted_count"],0)
        self.assertFalse(n["phase183_no_input_mode"]["blocking_failure"])

class TestPhase183Console(unittest.TestCase):
    def test_console(self):
        from smr_phase183_dirty_intelligence_inbox import build_console_integration
        c = build_console_integration()
        self.assertTrue(c["phase183_console_integration"]["inbox_viewable"])
        self.assertTrue(c["phase183_console_integration"]["console_not_auto_ingest"])

class TestPhase183Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase183_dirty_intelligence_inbox import build_phase183_guard
        g = build_phase183_guard()
        self.assertEqual(g["phase183_guard"]["status"],"pass")
        self.assertTrue(g["phase183_guard"]["full_raw_save_disabled"])
        self.assertTrue(g["phase183_guard"]["clean_evidence_write_disabled"])
        self.assertTrue(g["phase183_guard"]["llm_api_disabled"])

    def test_quality_gate(self):
        from smr_phase183_dirty_intelligence_inbox import build_phase183_quality_gate
        q = build_phase183_quality_gate()
        self.assertEqual(q["phase183_quality_gate"]["status"],"pass")
        self.assertEqual(q["phase183_quality_gate"]["violations"],0)
        self.assertTrue(q["phase183_quality_gate"]["checks"]["no_full_raw_save"])
        self.assertTrue(q["phase183_quality_gate"]["checks"]["no_clean_evidence"])

    def test_cc_guard(self):
        from smr_phase183_dirty_intelligence_inbox import build_phase183_cannot_conclude_guard
        c = build_phase183_cannot_conclude_guard()
        self.assertEqual(c["phase183_cannot_conclude_guard"]["status"],"pass")
        self.assertEqual(c["phase183_cannot_conclude_guard"]["violations"],0)
        self.assertIn("dirty_item_is_not_clean_evidence",c["phase183_cannot_conclude_guard"]["cannot_conclude"])

class TestPhase183Backlog(unittest.TestCase):
    def test_backlog(self):
        from smr_phase183_dirty_intelligence_inbox import build_backlog
        b = build_backlog()
        self.assertTrue(b["phase183_backlog"]["phase183_completed"])
        self.assertTrue(b["phase183_backlog"]["dirty_inbox_ready"])

class TestPhase183Reporting(unittest.TestCase):
    def test_inbox_board(self):
        from build_phase183_inbox_board import build_inbox_board
        b = build_inbox_board()
        self.assertEqual(b["phase183_inbox_board"]["guard"],"pass")
        self.assertEqual(b["phase183_inbox_board"]["violations"],0)
        self.assertTrue(b["phase183_inbox_board"]["accepted_manifest"]["manifest_is_dirty_not_clean"])

    def test_inbox_brief(self):
        from build_phase183_inbox_board import build_inbox_brief
        br = build_inbox_brief()
        self.assertTrue(br["phase183_inbox_brief"]["manifest_is_dirty_not_clean"])
        self.assertTrue(br["phase183_inbox_brief"]["dirty_to_clean_is_placeholder"])

    def test_dashboard(self):
        from build_phase183_inbox_board import build_dashboard
        d = build_dashboard()
        self.assertEqual(d["phase183_dashboard"]["summary"]["guard"],"pass")
        self.assertEqual(d["phase183_dashboard"]["summary"]["pending_created"],0)

class TestPhase183Pipeline(unittest.TestCase):
    def test_dry_run(self):
        from run_phase183_dirty_intelligence_inbox import run_pipeline
        r = run_pipeline("dry-run")
        p = r["phase183_dirty_intelligence_inbox_pipeline"]
        self.assertEqual(p["mode"],"dry-run")
        self.assertEqual(p["guard"],"pass")
        self.assertEqual(p["violations"],0)
        self.assertTrue(p["simulated"])
        self.assertGreater(p["accepted_count"],0)

    def test_execute(self):
        from run_phase183_dirty_intelligence_inbox import run_pipeline
        r = run_pipeline("execute")
        p = r["phase183_dirty_intelligence_inbox_pipeline"]
        self.assertEqual(p["mode"],"execute")
        self.assertEqual(p["quality_gate"],"pass")
        self.assertTrue(p["accepted_does_not_mean_clean_evidence"])
        self.assertFalse(p["llm_api_called"])
        self.assertFalse(p["raw_full_text_saved"])

    def test_skip_network(self):
        from run_phase183_dirty_intelligence_inbox import run_pipeline
        r = run_pipeline("skip-network")
        p = r["phase183_dirty_intelligence_inbox_pipeline"]
        self.assertEqual(p["mode"],"skip-network")
        self.assertEqual(p["cannot_conclude_guard"],"pass")

class TestPhase183Safety(unittest.TestCase):
    def test_no_llm_web_raw(self):
        from run_phase183_dirty_intelligence_inbox import run_pipeline
        for mode in ["dry-run","execute","skip-network"]:
            r = run_pipeline(mode)
            p = r["phase183_dirty_intelligence_inbox_pipeline"]
            self.assertFalse(p["llm_api_called"])
            self.assertFalse(p["web_search_called"])
            self.assertFalse(p["network_fetch_called"])
            self.assertFalse(p["raw_full_text_saved"])
            self.assertFalse(p["clean_evidence_written"])
            self.assertFalse(p["packet_updated"])

    def test_no_trade(self):
        from run_phase183_dirty_intelligence_inbox import run_pipeline
        r = run_pipeline("execute")
        p = r["phase183_dirty_intelligence_inbox_pipeline"]
        self.assertEqual(p["trade_recommendation_created"],0)
        self.assertEqual(p["target_price_created"],0)
        self.assertEqual(p["position_sizing_created"],0)
        self.assertEqual(p["pending_created"],0)

if __name__=="__main__":
    unittest.main()
