import unittest, json, sys, os
sys.path.insert(0,"08_scripts/lib"); sys.path.insert(0,"08_scripts/reporting"); sys.path.insert(0,"08_scripts/jobs")

class TestPhase188Registry(unittest.TestCase):
    def test_registry(self):
        from smr_phase188_real_source_lead_ingestion import build_ingestion_registry
        r = build_ingestion_registry()
        reg = r["phase188_ingestion_registry"]
        self.assertEqual(reg["source_lead_count"],6); self.assertTrue(reg["input_from_phase187"])
        self.assertTrue(reg["no_clean_evidence"])

class TestPhase188Converter(unittest.TestCase):
    def test_converter(self):
        from smr_phase188_real_source_lead_ingestion import build_source_lead_converter
        c = build_source_lead_converter()
        self.assertEqual(c["phase188_converted_items"]["converted_count"],6)
        self.assertTrue(c["phase188_converted_items"]["all_converted_not_clean_evidence"])
        for item in c["phase188_converted_items"]["converted_items"]:
            self.assertTrue(item["converted_not_clean_evidence"]); self.assertTrue(item["ready_for_dirty_inbox"])
            self.assertFalse(item["raw_full_text_saved"]); self.assertFalse(item["clean_evidence_created"])

class TestPhase188Metadata(unittest.TestCase):
    def test_metadata(self):
        from smr_phase188_real_source_lead_ingestion import build_metadata_validator
        m = build_metadata_validator()
        self.assertEqual(m["phase188_metadata_validation"]["items_checked"],6)
        self.assertTrue(m["phase188_metadata_validation"]["metadata_valid_does_not_mean_verified"])

class TestPhase188Copyright(unittest.TestCase):
    def test_copyright(self):
        from smr_phase188_real_source_lead_ingestion import build_copyright_validator
        c = build_copyright_validator()
        self.assertEqual(c["phase188_copyright_validation"]["items_checked"],6)
        self.assertTrue(c["phase188_copyright_validation"]["all_copyright_safe"])

class TestPhase188Dedup(unittest.TestCase):
    def test_dedup(self):
        from smr_phase188_real_source_lead_ingestion import build_ingestion_dedup
        d = build_ingestion_dedup()
        self.assertEqual(d["phase188_ingestion_dedup"]["items_checked"],6)
        self.assertEqual(d["phase188_ingestion_dedup"]["duplicates_found"],0)

class TestPhase188Manifest(unittest.TestCase):
    def test_manifest(self):
        from smr_phase188_real_source_lead_ingestion import build_ingestion_manifest
        m = build_ingestion_manifest()
        mm = m["phase188_ingestion_manifest"]
        self.assertTrue(mm["manifest_generated"]); self.assertEqual(mm["total_source_leads"],6)
        self.assertEqual(mm["ingested"],6); self.assertTrue(mm["ingested_not_clean_evidence"])

class TestPhase188CrossCheck(unittest.TestCase):
    def test_match_confirmation(self):
        from smr_phase188_real_source_lead_ingestion import build_cross_check_match_confirmation
        c = build_cross_check_match_confirmation()
        self.assertEqual(c["phase188_cross_check_match_confirmation"]["match_count"],6)
        self.assertTrue(c["phase188_cross_check_match_confirmation"]["all_matches_preview"])
        self.assertTrue(c["phase188_cross_check_match_confirmation"]["match_not_completed"])

class TestPhase188Verification(unittest.TestCase):
    def test_readiness(self):
        from smr_phase188_real_source_lead_ingestion import build_verification_readiness
        v = build_verification_readiness()
        self.assertTrue(v["phase188_verification_readiness"]["verification_readiness_not_clean_evidence_ready"])

class TestPhase188Eligibility(unittest.TestCase):
    def test_eligibility(self):
        from smr_phase188_real_source_lead_ingestion import build_eligibility_refresh
        e = build_eligibility_refresh()
        self.assertTrue(e["phase188_eligibility_refresh"]["would_be_requires_cross_check_first"])
        self.assertTrue(e["phase188_eligibility_refresh"]["would_be_not_clean_evidence_eligible_now"])

class TestPhase188Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase188_real_source_lead_ingestion import build_phase188_guard
        g = build_phase188_guard()
        self.assertEqual(g["phase188_guard"]["status"],"pass"); self.assertTrue(g["phase188_guard"]["ingestion_not_clean_evidence"])
    def test_quality_gate(self):
        from smr_phase188_real_source_lead_ingestion import build_phase188_quality_gate
        q = build_phase188_quality_gate()
        self.assertEqual(q["phase188_quality_gate"]["status"],"pass"); self.assertEqual(q["phase188_quality_gate"]["violations"],0)
    def test_cc_guard(self):
        from smr_phase188_real_source_lead_ingestion import build_phase188_cannot_conclude_guard
        c = build_phase188_cannot_conclude_guard()
        self.assertEqual(c["phase188_cannot_conclude_guard"]["status"],"pass")

class TestPhase188Reporting(unittest.TestCase):
    def test_board(self):
        from build_phase188_ingestion_board import build_ingestion_board
        b = build_ingestion_board(); self.assertEqual(b["phase188_ingestion_board"]["guard"],"pass")
    def test_brief(self):
        from build_phase188_ingestion_board import build_ingestion_brief
        br = build_ingestion_brief(); self.assertTrue(br["phase188_ingestion_brief"]["ingested_not_clean_evidence"])
    def test_dashboard(self):
        from build_phase188_ingestion_board import build_dashboard
        d = build_dashboard(); self.assertEqual(d["phase188_dashboard"]["summary"]["guard"],"pass")

class TestPhase188Pipeline(unittest.TestCase):
    def test_dry_run(self):
        from run_phase188_real_source_lead_ingestion import run_pipeline
        r = run_pipeline("dry-run")
        p = r["phase188_real_source_lead_ingestion_pipeline"]
        self.assertEqual(p["mode"],"dry-run"); self.assertEqual(p["guard"],"pass")
        self.assertEqual(p["converted_dirty_item_count"],6)
    def test_execute(self):
        from run_phase188_real_source_lead_ingestion import run_pipeline
        r = run_pipeline("execute")
        p = r["phase188_real_source_lead_ingestion_pipeline"]
        self.assertTrue(p["ingested_not_clean_evidence"]); self.assertTrue(p["metadata_valid_not_verified"])
        self.assertTrue(p["match_confirmed_preview_not_completed"])
    def test_skip_network(self):
        from run_phase188_real_source_lead_ingestion import run_pipeline
        r = run_pipeline("skip-network")
        self.assertEqual(r["phase188_real_source_lead_ingestion_pipeline"]["mode"],"skip-network")

class TestPhase188Safety(unittest.TestCase):
    def test_safety(self):
        from run_phase188_real_source_lead_ingestion import run_pipeline
        for mode in ["dry-run","execute","skip-network"]:
            r = run_pipeline(mode); p = r["phase188_real_source_lead_ingestion_pipeline"]
            self.assertFalse(p["clean_evidence_written"]); self.assertFalse(p["llm_api_called"])
            self.assertFalse(p["raw_full_text_saved"]); self.assertFalse(p["network_fetch_called"])
    def test_no_trade(self):
        from run_phase188_real_source_lead_ingestion import run_pipeline
        r = run_pipeline("execute")
        p = r["phase188_real_source_lead_ingestion_pipeline"]
        self.assertEqual(p["trade_recommendation_created"],0); self.assertEqual(p["target_price_created"],0)
        self.assertEqual(p["position_sizing_created"],0); self.assertEqual(p["broker_api_called"],False)

if __name__=="__main__": unittest.main()
