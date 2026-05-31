import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

class TestPhase92Config(unittest.TestCase):
    def test_load(self):
        from smr_phase92_config import load_config
        cfg=load_config()
        self.assertEqual(cfg["phase"],"phase92")
    def test_universe(self):
        from smr_phase92_config import get_universe
        self.assertEqual(len(get_universe()),8)
    def test_signals(self):
        from smr_phase92_config import get_signal_types
        self.assertEqual(len(get_signal_types()),10)
    def test_keywords(self):
        from smr_phase92_config import get_keywords
        self.assertGreater(len(get_keywords("cn")),10)
    def test_no_mock(self):
        from smr_phase92_config import load_config
        self.assertFalse(load_config()["safety"]["mock_allowed"])
    def test_no_trade(self):
        from smr_phase92_config import load_config
        c=load_config()["safety"]
        self.assertFalse(c["real_trade_allowed"])
        self.assertFalse(c["pending_allowed"])

class TestRegistry(unittest.TestCase):
    def test_build(self):
        from smr_phase92_order_source_registry import build_order_source_registry
        r=build_order_source_registry()
        self.assertGreater(r["phase92_order_source_registry"]["order_sources_registered"],10)
    def test_has_cninfo(self):
        from smr_phase92_order_source_registry import build_order_source_registry
        r=build_order_source_registry()
        ids=[s["source_id"] for s in r["phase92_order_source_registry"]["sources"]]
        self.assertIn("cninfo_keyword_search",ids)
    def test_has_tender(self):
        from smr_phase92_order_source_registry import build_order_source_registry
        r=build_order_source_registry()
        ids=[s["source_id"] for s in r["phase92_order_source_registry"]["sources"]]
        self.assertIn("china_tender_platform",ids)

class TestEntityResolver(unittest.TestCase):
    def test_build(self):
        from smr_phase92_ticker_entity_resolver import build_ticker_entity_resolver
        r=build_ticker_entity_resolver()
        self.assertEqual(r["phase92_ticker_entity_resolver"]["tickers_resolved"],8)
    def test_300394_blocked(self):
        from smr_phase92_ticker_entity_resolver import build_ticker_entity_resolver
        r=build_ticker_entity_resolver()
        e=[e for e in r["phase92_ticker_entity_resolver"]["entities"] if e["ticker"]=="300394.SZ"][0]
        self.assertTrue(e["blocked"])
    def test_no_mock(self):
        from smr_phase92_ticker_entity_resolver import build_ticker_entity_resolver
        r=build_ticker_entity_resolver()
        self.assertFalse(r["phase92_ticker_entity_resolver"]["mock_used"])

class TestExploration(unittest.TestCase):
    def test_dry_run(self):
        from smr_phase92_order_source_exploration import explore_order_sources
        r=explore_order_sources("dry-run")
        self.assertEqual(r["phase92_order_source_exploration"]["mode"],"dry-run")
    def test_execute(self):
        from smr_phase92_order_source_exploration import explore_order_sources
        r=explore_order_sources("execute")
        self.assertEqual(r["phase92_order_source_exploration"]["mode"],"execute")
        self.assertGreater(r["phase92_order_source_exploration"]["sources_attempted"],0)
    def test_skip_network(self):
        from smr_phase92_order_source_exploration import explore_order_sources
        r=explore_order_sources("skip-network")
        self.assertEqual(r["phase92_order_source_exploration"]["mode"],"skip-network")
    def test_8_tickers(self):
        from smr_phase92_order_source_exploration import explore_order_sources
        r=explore_order_sources("execute")
        self.assertEqual(r["phase92_order_source_exploration"]["tickers_explored"],8)
    def test_no_mock(self):
        from smr_phase92_order_source_exploration import explore_order_sources
        r=explore_order_sources("dry-run")
        self.assertFalse(r["phase92_order_source_exploration"]["mock_used"])

class TestSignalClassifier(unittest.TestCase):
    def test_classify(self):
        from smr_phase92_order_source_exploration import explore_order_sources
        from smr_phase92_order_text_collector import collect_order_texts
        from smr_phase92_order_signal_classifier import classify_order_signals
        exp=explore_order_sources("execute")
        texts=collect_order_texts(exp)
        r=classify_order_signals(texts)
        self.assertGreater(r["phase92_order_signal_classifier"]["total_signals_classified"],0)
    def test_no_mock(self):
        from smr_phase92_order_source_exploration import explore_order_sources
        from smr_phase92_order_text_collector import collect_order_texts
        from smr_phase92_order_signal_classifier import classify_order_signals
        exp=explore_order_sources("execute")
        texts=collect_order_texts(exp)
        r=classify_order_signals(texts)
        self.assertFalse(r["phase92_order_signal_classifier"]["mock_used"])

class TestEvidence(unittest.TestCase):
    def test_extract(self):
        from smr_phase92_order_source_exploration import explore_order_sources
        from smr_phase92_order_text_collector import collect_order_texts
        from smr_phase92_order_signal_classifier import classify_order_signals
        from smr_phase92_order_evidence_extraction import extract_order_evidence
        exp=explore_order_sources("execute")
        texts=collect_order_texts(exp)
        sigs=classify_order_signals(texts)
        r=extract_order_evidence(sigs)
        self.assertGreater(len(r["phase92_order_evidence_extraction"]["evidence_records"]),0)
    def test_cannot_conclude(self):
        from smr_phase92_order_source_exploration import explore_order_sources
        from smr_phase92_order_text_collector import collect_order_texts
        from smr_phase92_order_signal_classifier import classify_order_signals
        from smr_phase92_order_evidence_extraction import extract_order_evidence
        exp=explore_order_sources("execute")
        texts=collect_order_texts(exp)
        sigs=classify_order_signals(texts)
        r=extract_order_evidence(sigs)
        for rec in r["phase92_order_evidence_extraction"]["evidence_records"]:
            for item in rec["evidence_items"]:
                self.assertIn("cannot_conclude",item)
    def test_no_mock(self):
        from smr_phase92_order_source_exploration import explore_order_sources
        from smr_phase92_order_text_collector import collect_order_texts
        from smr_phase92_order_signal_classifier import classify_order_signals
        from smr_phase92_order_evidence_extraction import extract_order_evidence
        exp=explore_order_sources("execute")
        texts=collect_order_texts(exp)
        sigs=classify_order_signals(texts)
        r=extract_order_evidence(sigs)
        self.assertFalse(r["phase92_order_evidence_extraction"]["mock_used"])

class TestQualityGate(unittest.TestCase):
    def test_gate(self):
        from smr_phase92_order_source_exploration import explore_order_sources
        from smr_phase92_order_text_collector import collect_order_texts
        from smr_phase92_order_signal_classifier import classify_order_signals
        from smr_phase92_order_evidence_extraction import extract_order_evidence
        from smr_phase92_order_quality_gate import run_quality_gate
        exp=explore_order_sources("execute")
        texts=collect_order_texts(exp)
        sigs=classify_order_signals(texts)
        ev=extract_order_evidence(sigs)
        r=run_quality_gate(ev)
        gs=r["phase92_order_quality_gate"]["gate_summary"]
        self.assertGreaterEqual(gs["passed"]+gs["review_required"]+gs["rejected"],1)
    def test_no_mock(self):
        from smr_phase92_order_source_exploration import explore_order_sources
        from smr_phase92_order_text_collector import collect_order_texts
        from smr_phase92_order_signal_classifier import classify_order_signals
        from smr_phase92_order_evidence_extraction import extract_order_evidence
        from smr_phase92_order_quality_gate import run_quality_gate
        exp=explore_order_sources("execute")
        texts=collect_order_texts(exp)
        sigs=classify_order_signals(texts)
        ev=extract_order_evidence(sigs)
        r=run_quality_gate(ev)
        self.assertFalse(r["phase92_order_quality_gate"]["mock_used"])

class TestGuard(unittest.TestCase):
    def test_pass(self):
        from smr_phase92_order_source_exploration import explore_order_sources
        from smr_phase92_order_text_collector import collect_order_texts
        from smr_phase92_order_signal_classifier import classify_order_signals
        from smr_phase92_order_evidence_extraction import extract_order_evidence
        from smr_phase92_order_quality_gate import run_quality_gate
        from smr_phase92_cannot_conclude_guard import run_cannot_conclude_guard
        exp=explore_order_sources("execute")
        texts=collect_order_texts(exp)
        sigs=classify_order_signals(texts)
        ev=extract_order_evidence(sigs)
        gate=run_quality_gate(ev)
        r=run_cannot_conclude_guard(ev,gate)
        self.assertEqual(r["phase92_cannot_conclude_guard"]["violations_found"],0)
    def test_status(self):
        from smr_phase92_order_source_exploration import explore_order_sources
        from smr_phase92_order_text_collector import collect_order_texts
        from smr_phase92_order_signal_classifier import classify_order_signals
        from smr_phase92_order_evidence_extraction import extract_order_evidence
        from smr_phase92_order_quality_gate import run_quality_gate
        from smr_phase92_cannot_conclude_guard import run_cannot_conclude_guard
        exp=explore_order_sources("execute")
        texts=collect_order_texts(exp)
        sigs=classify_order_signals(texts)
        ev=extract_order_evidence(sigs)
        gate=run_quality_gate(ev)
        r=run_cannot_conclude_guard(ev,gate)
        self.assertEqual(r["phase92_cannot_conclude_guard"]["overall_status"],"pass")

class TestCoverageMatrix(unittest.TestCase):
    def test_matrix(self):
        from smr_phase92_order_source_exploration import explore_order_sources
        from smr_phase92_order_coverage_matrix import build_order_coverage_matrix
        exp=explore_order_sources("execute")
        r=build_order_coverage_matrix(exp)
        self.assertEqual(r["phase92_order_source_coverage_matrix"]["tickers_total"],8)
    def test_300394_blocked(self):
        from smr_phase92_order_source_exploration import explore_order_sources
        from smr_phase92_order_coverage_matrix import build_order_coverage_matrix
        exp=explore_order_sources("execute")
        r=build_order_coverage_matrix(exp)
        rows=r["phase92_order_source_coverage_matrix"]["coverage_rows"]
        row=[row for row in rows if row["ticker"]=="300394.SZ"][0]
        self.assertEqual(row["order_contract_coverage_status"],"blocked")
    def test_no_mock(self):
        from smr_phase92_order_source_exploration import explore_order_sources
        from smr_phase92_order_coverage_matrix import build_order_coverage_matrix
        exp=explore_order_sources("execute")
        r=build_order_coverage_matrix(exp)
        self.assertFalse(r["phase92_order_source_coverage_matrix"]["mock_used"])

class TestGapCloseout(unittest.TestCase):
    def test_closeout(self):
        from smr_phase92_order_source_exploration import explore_order_sources
        from smr_phase92_order_coverage_matrix import build_order_coverage_matrix
        from smr_phase92_gap_closeout import build_gap_closeout
        exp=explore_order_sources("execute")
        matrix=build_order_coverage_matrix(exp)
        r=build_gap_closeout(matrix,exp)
        self.assertEqual(r["phase92_order_hard_data_gap_closeout"]["total_tickers"],8)
    def test_no_mock(self):
        from smr_phase92_order_source_exploration import explore_order_sources
        from smr_phase92_order_coverage_matrix import build_order_coverage_matrix
        from smr_phase92_gap_closeout import build_gap_closeout
        exp=explore_order_sources("execute")
        matrix=build_order_coverage_matrix(exp)
        r=build_gap_closeout(matrix,exp)
        self.assertFalse(r["phase92_order_hard_data_gap_closeout"]["mock_used"])

class TestBacklog(unittest.TestCase):
    def test_build(self):
        from smr_phase92_backlog_update import build_backlog_update
        r=build_backlog_update()
        self.assertEqual(r["phase92_backlog_update"]["backlog_items"],10)
    def test_recommendation(self):
        from smr_phase92_backlog_update import build_backlog_update
        r=build_backlog_update()
        self.assertIn("customer_capex",r["phase92_backlog_update"]["phase93_recommendation"])
    def test_no_mock(self):
        from smr_phase92_backlog_update import build_backlog_update
        r=build_backlog_update()
        self.assertFalse(r["phase92_backlog_update"]["mock_used"])

class TestRunner(unittest.TestCase):
    def test_dry_run(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase92_order_hard_source_pipeline import main as rmain
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rmain()
            d=json.loads(buf.getvalue())
            self.assertEqual(d["phase92_order_hard_source_pipeline"]["mode"],"dry-run")
        finally:sys.argv=o
    def test_execute(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase92_order_hard_source_pipeline import main as rmain
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rmain()
            d=json.loads(buf.getvalue())
            p=d["phase92_order_hard_source_pipeline"]
            self.assertEqual(p["mode"],"execute")
            self.assertEqual(p["tickers_explored"],8)
        finally:sys.argv=o
    def test_skip_network(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase92_order_hard_source_pipeline import main as rmain
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rmain()
            d=json.loads(buf.getvalue())
            self.assertEqual(d["phase92_order_hard_source_pipeline"]["mode"],"skip-network")
        finally:sys.argv=o
    def test_no_pending(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase92_order_hard_source_pipeline import main as rmain
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rmain()
            d=json.loads(buf.getvalue())
            p=d["phase92_order_hard_source_pipeline"]
            self.assertEqual(p["pending_created"],0)
            self.assertEqual(p["real_trade_created"],0)
            self.assertFalse(p["mock_used"])
        finally:sys.argv=o

class TestDashboard(unittest.TestCase):
    def test_json(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase92_order_hard_source_dashboard import main as dmain
        o=sys.argv[:]
        try:
            sys.argv=["d.py","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dmain()
            d=json.loads(buf.getvalue())
            self.assertIn("order_sources_registered",d["summary"])
        finally:sys.argv=o
    def test_no_mock(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase92_order_hard_source_dashboard import main as dmain
        o=sys.argv[:]
        try:
            sys.argv=["d.py","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dmain()
            d=json.loads(buf.getvalue())
            self.assertFalse(d["summary"]["mock_used"])
        finally:sys.argv=o
    def test_no_pending(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase92_order_hard_source_dashboard import main as dmain
        o=sys.argv[:]
        try:
            sys.argv=["d.py","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dmain()
            d=json.loads(buf.getvalue())
            self.assertEqual(d["summary"]["pending_created"],0)
        finally:sys.argv=o

if __name__=="__main__":
    unittest.main()
