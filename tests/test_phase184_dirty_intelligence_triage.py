import unittest, json, sys, os
sys.path.insert(0,"08_scripts/lib"); sys.path.insert(0,"08_scripts/reporting"); sys.path.insert(0,"08_scripts/jobs")

class TestPhase184TriageTaxonomy(unittest.TestCase):
    def test_taxonomy(self):
        from smr_phase184_dirty_intelligence_triage import build_triage_taxonomy
        t = build_triage_taxonomy()
        tx = t["phase184_triage_taxonomy"]
        self.assertEqual(tx["category_count"],7)
        self.assertTrue(tx["all_categories_are_dirty_not_clean"])
        for c in tx["triage_categories"]:
            self.assertFalse(c["is_clean_evidence"])
            self.assertFalse(c["is_verified"])

class TestPhase184ClassificationRules(unittest.TestCase):
    def test_rules(self):
        from smr_phase184_dirty_intelligence_triage import build_classification_rule_registry
        r = build_classification_rule_registry()
        self.assertEqual(r["phase184_classification_rules"]["rule_count"],7)
        for rule in r["phase184_classification_rules"]["rules"]:
            self.assertIn("rule_id",rule)
            self.assertIn("primary",rule)

class TestPhase184Scoring(unittest.TestCase):
    def test_source_reliability(self):
        from smr_phase184_dirty_intelligence_triage import build_source_reliability_pre_score
        s = build_source_reliability_pre_score()
        self.assertEqual(s["phase184_source_reliability"]["items_scored"],8)

    def test_relevance(self):
        from smr_phase184_dirty_intelligence_triage import build_relevance_scorer
        r = build_relevance_scorer()
        self.assertEqual(r["phase184_relevance_scorer"]["items_scored"],8)
        self.assertTrue(r["phase184_relevance_scorer"]["scoring_not_stock_rating"])

    def test_freshness(self):
        from smr_phase184_dirty_intelligence_triage import build_freshness_scorer
        f = build_freshness_scorer()
        self.assertEqual(f["phase184_freshness_scorer"]["items_scored"],8)

    def test_directness(self):
        from smr_phase184_dirty_intelligence_triage import build_directness_scorer
        d = build_directness_scorer()
        self.assertEqual(d["phase184_directness_scorer"]["items_scored"],8)

    def test_evidence_candidacy(self):
        from smr_phase184_dirty_intelligence_triage import build_evidence_candidacy_scorer
        e = build_evidence_candidacy_scorer()
        self.assertEqual(e["phase184_evidence_candidacy_scorer"]["items_scored"],8)
        self.assertTrue(e["phase184_evidence_candidacy_scorer"]["scoring_not_stock_rating"])

class TestPhase184Classifiers(unittest.TestCase):
    def test_cross_check(self):
        from smr_phase184_dirty_intelligence_triage import build_cross_check_need_classifier
        c = build_cross_check_need_classifier()
        self.assertEqual(c["phase184_cross_check_classifier"]["items_checked"],8)
        self.assertTrue(c["phase184_cross_check_classifier"]["cross_check_not_verified"])

    def test_owner_review(self):
        from smr_phase184_dirty_intelligence_triage import build_owner_review_need_classifier
        o = build_owner_review_need_classifier()
        self.assertEqual(o["phase184_owner_review_classifier"]["items_checked"],8)
        self.assertTrue(o["phase184_owner_review_classifier"]["owner_review_not_owner_approved"])

    def test_discard(self):
        from smr_phase184_dirty_intelligence_triage import build_discard_classifier
        d = build_discard_classifier()
        self.assertEqual(d["phase184_discard_classifier"]["items_checked"],8)

class TestPhase184TriageDecisions(unittest.TestCase):
    def test_decision_builder(self):
        from smr_phase184_dirty_intelligence_triage import build_triage_decision_builder
        d = build_triage_decision_builder()
        td = d["phase184_triage_decisions"]
        self.assertEqual(td["items_triaged"],8)
        total = td["discard_count"]+td["duplicate_count"]+td["source_lead_count"]+td["candidate_evidence_count"]+td["cross_check_count"]+td["owner_review_count"]+td["quarantined_count"]
        self.assertEqual(total,8)
        for dec in td["decisions"]:
            self.assertTrue(dec["triage_is_not_stock_rating"])
            self.assertTrue(dec["triage_is_not_clean_evidence"])

class TestPhase184Manifest(unittest.TestCase):
    def test_triage_manifest(self):
        from smr_phase184_dirty_intelligence_triage import build_triage_manifest
        m = build_triage_manifest()
        tm = m["phase184_triage_manifest"]
        self.assertTrue(tm["manifest_generated"])
        self.assertTrue(tm["candidate_evidence_not_clean_evidence"])
        self.assertTrue(tm["source_lead_not_confirmed"])
        self.assertTrue(tm["cross_check_not_verified"])
        self.assertTrue(tm["owner_review_not_approved"])

class TestPhase184Queues(unittest.TestCase):
    def test_cleaning_queue(self):
        from smr_phase184_dirty_intelligence_triage import build_cleaning_queue_preview
        c = build_cleaning_queue_preview()
        self.assertTrue(c["phase184_cleaning_queue_preview"]["cleaning_not_started"])
        self.assertTrue(c["phase184_cleaning_queue_preview"]["auto_clean_disabled"])

    def test_cross_check_routing(self):
        from smr_phase184_dirty_intelligence_triage import build_cross_check_routing_preview
        c = build_cross_check_routing_preview()
        self.assertTrue(c["phase184_cross_check_routing"]["cross_check_not_executed"])

    def test_source_lead_queue(self):
        from smr_phase184_dirty_intelligence_triage import build_source_lead_queue_preview
        s = build_source_lead_queue_preview()
        self.assertTrue(s["phase184_source_lead_queue"]["source_lead_not_confirmed_fact"])

    def test_candidate_evidence_queue(self):
        from smr_phase184_dirty_intelligence_triage import build_candidate_evidence_queue_preview
        c = build_candidate_evidence_queue_preview()
        self.assertTrue(c["phase184_candidate_evidence_queue"]["candidate_not_clean_evidence"])
        self.assertTrue(c["phase184_candidate_evidence_queue"]["candidate_not_verified"])

    def test_owner_review_queue(self):
        from smr_phase184_dirty_intelligence_triage import build_owner_review_queue_preview
        o = build_owner_review_queue_preview()
        self.assertTrue(o["phase184_owner_review_queue"]["owner_review_not_owner_approved"])
        self.assertTrue(o["phase184_owner_review_queue"]["owner_must_manually_review"])

class TestPhase184Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase184_dirty_intelligence_triage import build_phase184_guard
        g = build_phase184_guard()
        self.assertEqual(g["phase184_guard"]["status"],"pass")
        self.assertTrue(g["phase184_guard"]["clean_evidence_write_disabled"])
        self.assertTrue(g["phase184_guard"]["auto_clean_disabled"])

    def test_quality_gate(self):
        from smr_phase184_dirty_intelligence_triage import build_phase184_quality_gate
        q = build_phase184_quality_gate()
        self.assertEqual(q["phase184_quality_gate"]["status"],"pass")
        self.assertEqual(q["phase184_quality_gate"]["violations"],0)
        self.assertTrue(q["phase184_quality_gate"]["checks"]["triage_score_not_stock_rating"])

    def test_cc_guard(self):
        from smr_phase184_dirty_intelligence_triage import build_phase184_cannot_conclude_guard
        c = build_phase184_cannot_conclude_guard()
        self.assertEqual(c["phase184_cannot_conclude_guard"]["status"],"pass")
        self.assertIn("candidate_evidence_candidate_is_not_clean_evidence",c["phase184_cannot_conclude_guard"]["cannot_conclude"])

class TestPhase184Reporting(unittest.TestCase):
    def test_triage_board(self):
        from build_phase184_triage_board import build_triage_board
        b = build_triage_board()
        self.assertEqual(b["phase184_triage_board"]["guard"],"pass")

    def test_triage_brief(self):
        from build_phase184_triage_board import build_triage_brief
        br = build_triage_brief()
        self.assertEqual(br["phase184_triage_brief"]["items_triaged"],8)
        self.assertTrue(br["phase184_triage_brief"]["triage_score_not_stock_rating"])

    def test_dashboard(self):
        from build_phase184_triage_board import build_dashboard
        d = build_dashboard()
        self.assertEqual(d["phase184_dashboard"]["summary"]["guard"],"pass")

class TestPhase184Pipeline(unittest.TestCase):
    def test_dry_run(self):
        from run_phase184_dirty_intelligence_triage import run_pipeline
        r = run_pipeline("dry-run")
        p = r["phase184_dirty_intelligence_triage_pipeline"]
        self.assertEqual(p["mode"],"dry-run"); self.assertEqual(p["guard"],"pass")
        self.assertEqual(p["items_triaged"],8); self.assertTrue(p["candidate_evidence_not_clean_evidence"])

    def test_execute(self):
        from run_phase184_dirty_intelligence_triage import run_pipeline
        r = run_pipeline("execute")
        p = r["phase184_dirty_intelligence_triage_pipeline"]
        self.assertEqual(p["mode"],"execute"); self.assertTrue(p["triage_score_not_stock_rating"])
        self.assertTrue(p["source_lead_not_confirmed_fact"]); self.assertTrue(p["cross_check_not_verified"])

    def test_skip_network(self):
        from run_phase184_dirty_intelligence_triage import run_pipeline
        r = run_pipeline("skip-network")
        p = r["phase184_dirty_intelligence_triage_pipeline"]
        self.assertEqual(p["mode"],"skip-network"); self.assertEqual(p["quality_gate"],"pass")

class TestPhase184Safety(unittest.TestCase):
    def test_no_llm_clean(self):
        from run_phase184_dirty_intelligence_triage import run_pipeline
        for mode in ["dry-run","execute","skip-network"]:
            r = run_pipeline(mode); p = r["phase184_dirty_intelligence_triage_pipeline"]
            self.assertFalse(p["llm_api_called"]); self.assertFalse(p["web_search_called"])
            self.assertFalse(p["clean_evidence_written"]); self.assertFalse(p["packet_updated"])

    def test_no_trade(self):
        from run_phase184_dirty_intelligence_triage import run_pipeline
        r = run_pipeline("execute")
        p = r["phase184_dirty_intelligence_triage_pipeline"]
        self.assertEqual(p["trade_recommendation_created"],0); self.assertEqual(p["target_price_created"],0)
        self.assertEqual(p["position_sizing_created"],0); self.assertEqual(p["pending_created"],0)

if __name__=="__main__": unittest.main()
