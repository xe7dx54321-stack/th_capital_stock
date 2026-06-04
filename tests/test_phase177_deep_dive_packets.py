import unittest, json, sys, os
sys.path.insert(0,"08_scripts/lib"); sys.path.insert(0,"08_scripts/reporting"); sys.path.insert(0,"08_scripts/jobs")

class TestPhase177Packets(unittest.TestCase):
    def test_packet_count(self):
        from smr_phase177_packet_builder import build_all_packets
        p = build_all_packets()
        pp = p["phase177_deep_dive_packets"]
        self.assertEqual(pp["activated_candidate_count"],9)
        self.assertEqual(pp["formal_packet_count"],9)
        self.assertEqual(pp["keep_summary_count"],2)
        self.assertEqual(pp["defer_summary_count"],1)
        self.assertEqual(pp["reject_summary_count"],1)

    def test_single_packet_structure(self):
        from smr_phase177_packet_builder import build_single_packet
        pkt = build_single_packet("MRVL")
        self.assertEqual(pkt["candidate_id"],"MRVL")
        self.assertIn("evidence_summary",pkt)
        self.assertIn("thesis_seed_summary",pkt)
        self.assertIn("risk_and_limitation_summary",pkt)
        self.assertIn("source_coverage_summary",pkt)
        self.assertIn("gap_register",pkt)
        self.assertIn("next_research_actions",pkt)
        self.assertIn("completeness_score",pkt)
        self.assertTrue(pkt["completeness_score_is_research_completeness_not_stock_rating"])

    def test_all_packets_have_required_fields(self):
        from smr_phase177_packet_builder import build_all_packets, ACTIVATED
        p = build_all_packets()
        for pkt in p["phase177_deep_dive_packets"]["packets"]:
            self.assertTrue(pkt["research_only"])
            self.assertTrue(pkt["not_trade_advice"])
            self.assertTrue(pkt["thesis_seed_summary"]["thesis_not_confirmed"])
            self.assertGreater(pkt["completeness_score"],0)

    def test_no_trade_terms_in_packets(self):
        from smr_phase177_packet_builder import build_all_packets
        p = build_all_packets()
        p_str = json.dumps(p,ensure_ascii=False).lower()
        for term in ["buy "," sell "," hold ","trade_order","target_price","position_size"]:
            self.assertNotIn(term, p_str)

class TestPhase177Guards(unittest.TestCase):
    def test_quality_gate(self):
        from smr_phase177_packet_builder import build_packet_quality_gate
        q = build_packet_quality_gate()
        self.assertEqual(q["phase177_packet_quality_gate"]["status"],"pass")
        self.assertEqual(q["phase177_packet_quality_gate"]["violations"],0)

    def test_guard(self):
        from smr_phase177_packet_builder import build_phase177_guard
        g = build_phase177_guard()
        self.assertEqual(g["phase177_guard"]["status"],"pass")

    def test_cc(self):
        from smr_phase177_packet_builder import build_phase177_cannot_conclude_guard
        c = build_phase177_cannot_conclude_guard()
        self.assertEqual(c["phase177_cannot_conclude_guard"]["status"],"pass")

    def test_owner_review_queue(self):
        from smr_phase177_packet_builder import build_owner_review_queue
        q = build_owner_review_queue()
        self.assertEqual(q["phase177_owner_review_queue"]["queue_count"],9)
        self.assertTrue(q["phase177_owner_review_queue"]["review_is_read_only"])

class TestPhase177Reporting(unittest.TestCase):
    def test_board(self):
        from build_phase177_packet_board import build_packet_board
        b = build_packet_board()
        self.assertEqual(b["phase177_deep_dive_packets"]["formal_packet_count"],9)

    def test_dashboard(self):
        from build_phase177_packet_board import build_dashboard
        d = build_dashboard()
        self.assertEqual(d["phase177_dashboard"]["summary"]["packets"],9)

    def test_console(self):
        from build_phase177_packet_board import build_console_integration
        c = build_console_integration()
        self.assertTrue(c["phase177_console_integration"]["deep_dive_packets_linked"])

class TestPhase177Pipeline(unittest.TestCase):
    def test_dry_run(self):
        from run_phase177_deep_dive_packet_generation import run_pipeline
        r = run_pipeline("dry-run")
        self.assertEqual(r["phase177_deep_dive_packet_pipeline"]["mode"],"dry-run")
        self.assertEqual(r["phase177_deep_dive_packet_pipeline"]["guard"],"pass")

    def test_execute(self):
        from run_phase177_deep_dive_packet_generation import run_pipeline
        r = run_pipeline("execute")
        self.assertEqual(r["phase177_deep_dive_packet_pipeline"]["formal_packet_count"],9)
        self.assertTrue(r["phase177_deep_dive_packet_pipeline"]["packets_written_to_generated"])

    def test_skip_network(self):
        from run_phase177_deep_dive_packet_generation import run_pipeline
        r = run_pipeline("skip-network")
        self.assertEqual(r["phase177_deep_dive_packet_pipeline"]["mode"],"skip-network")

if __name__=="__main__":
    unittest.main()
