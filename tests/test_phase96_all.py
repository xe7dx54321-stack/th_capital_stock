import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

class TestPhase96Config(unittest.TestCase):
    def test_load(self):
        from smr_phase96_config import load_config
        self.assertEqual(load_config()["phase"],"phase96")
    def test_universe(self):
        from smr_phase96_config import get_universe
        self.assertEqual(len(get_universe()),8)
    def test_peer_groups(self):
        from smr_phase96_config import get_peer_groups
        self.assertGreaterEqual(len(get_peer_groups()),4)
    def test_db_ignored(self):
        from smr_phase96_config import load_config
        self.assertTrue(load_config()["db"]["gitignored"])
    def test_no_mock(self):
        from smr_phase96_config import load_config
        self.assertFalse(load_config()["safety"]["mock_allowed"])

class TestPhase96DBSchema(unittest.TestCase):
    def test_schema(self):
        from smr_phase96_db_schema import build_hard_data_db_schema
        r=build_hard_data_db_schema()
        self.assertGreater(r["phase96_hard_data_db_schema"]["total_fields"],10)

class TestPhase96EvidenceLoader(unittest.TestCase):
    def test_load(self):
        from smr_phase96_evidence_loader import load_phase92_95_evidence
        r=load_phase92_95_evidence()
        self.assertGreater(r["phase96_evidence_loader"]["records_loaded"],0)
    def test_8_tickers(self):
        from smr_phase96_evidence_loader import load_phase92_95_evidence
        r=load_phase92_95_evidence()
        tickers=set(rec["ticker"] for rec in r["phase96_evidence_loader"]["records"])
        self.assertEqual(len(tickers),8)
    def test_6_categories(self):
        from smr_phase96_evidence_loader import load_phase92_95_evidence
        r=load_phase92_95_evidence()
        cats=set(rec["hard_data_category"] for rec in r["phase96_evidence_loader"]["records"])
        self.assertEqual(len(cats),6)

class TestPhase96Normalizer(unittest.TestCase):
    def test_normalize(self):
        from smr_phase96_evidence_loader import load_phase92_95_evidence
        from smr_phase96_hard_data_normalizer import normalize_hard_data_records
        ev=load_phase92_95_evidence()
        r=normalize_hard_data_records(ev["phase96_evidence_loader"]["records"])
        self.assertGreater(r["phase96_hard_data_normalization"]["records_normalized"],0)

class TestPhase96DBWriter(unittest.TestCase):
    def test_dry(self):
        from smr_phase96_db_writer import write_hard_data_db
        r=write_hard_data_db([{"ticker":"TEST","hard_data_category":"test"}],"dry-run")
        self.assertEqual(r["mode"],"dry-run");self.assertTrue(r["db_path_ignored"])
    def test_execute(self):
        from smr_phase96_db_writer import write_hard_data_db
        r=write_hard_data_db([{"ticker":"TEST","hard_data_category":"test","data_type":"text_evidence","record_id":"test-1"}],"execute")
        self.assertTrue(r["db_path_ignored"])

class TestPhase96TickerProfile(unittest.TestCase):
    def test_profile(self):
        from smr_phase96_evidence_loader import load_phase92_95_evidence
        from smr_phase96_ticker_profile import build_ticker_hard_data_profiles
        ev=load_phase92_95_evidence()
        r=build_ticker_hard_data_profiles(ev["phase96_evidence_loader"]["records"])
        self.assertEqual(r["phase96_ticker_hard_data_profile"]["tickers_profiled"],8)

class TestPhase96PeerRegistry(unittest.TestCase):
    def test_registry(self):
        from smr_phase96_peer_group_registry import build_peer_group_registry
        r=build_peer_group_registry()
        self.assertGreaterEqual(r["phase96_peer_group_registry"]["peer_groups_created"],4)
    def test_all_tickers_mapped(self):
        from smr_phase96_peer_group_registry import build_peer_group_registry
        r=build_peer_group_registry()
        tickers=set(m["ticker"] for m in r["phase96_peer_group_registry"]["ticker_mappings"])
        self.assertEqual(len(tickers),8)

class TestPhase96PeerBenchmarkMatrix(unittest.TestCase):
    def test_matrix(self):
        from smr_phase96_evidence_loader import load_phase92_95_evidence
        from smr_phase96_ticker_profile import build_ticker_hard_data_profiles
        from smr_phase96_peer_benchmark_matrix import build_peer_benchmark_matrix
        ev=load_phase92_95_evidence();prof=build_ticker_hard_data_profiles(ev["phase96_evidence_loader"]["records"])
        r=build_peer_benchmark_matrix(ev["phase96_evidence_loader"]["records"],prof)
        self.assertEqual(r["phase96_peer_benchmark_matrix"]["tickers"],8)

class TestPhase96FieldMissingness(unittest.TestCase):
    def test_report(self):
        from smr_phase96_evidence_loader import load_phase92_95_evidence
        from smr_phase96_field_missingness import build_field_missingness_report
        ev=load_phase92_95_evidence()
        r=build_field_missingness_report(ev["phase96_evidence_loader"]["records"])
        self.assertIn("critical_missing_fields",r["phase96_field_missingness_report"])

class TestPhase96QualityGate(unittest.TestCase):
    def test_gate(self):
        from smr_phase96_evidence_loader import load_phase92_95_evidence
        from smr_phase96_quality_gate import run_db_quality_gate
        ev=load_phase92_95_evidence()
        r=run_db_quality_gate(ev["phase96_evidence_loader"]["records"])
        self.assertEqual(r["phase96_db_quality_gate"]["overall"],"pass")

class TestPhase96Guard(unittest.TestCase):
    def test_guard(self):
        from smr_phase96_evidence_loader import load_phase92_95_evidence
        from smr_phase96_cannot_conclude_guard import run_peer_benchmark_cannot_conclude_guard
        ev=load_phase92_95_evidence()
        r=run_peer_benchmark_cannot_conclude_guard(ev["phase96_evidence_loader"]["records"])
        self.assertEqual(r["phase96_peer_benchmark_cannot_conclude_guard"]["overall"],"pass")

class TestPhase96Backlog(unittest.TestCase):
    def test_backlog(self):
        from smr_phase96_backlog_update import build_backlog_update
        r=build_backlog_update()
        self.assertGreater(r["phase96_backlog_update"]["items"],5)
    def test_phase97(self):
        from smr_phase96_backlog_update import build_backlog_update
        self.assertIn("phase97_recommendation",build_backlog_update()["phase96_backlog_update"])

class TestPhase96Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase96_peer_benchmark_hard_data_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase96_pipeline"]
            self.assertEqual(d["mode"],"dry-run");self.assertEqual(d["tickers"],8)
        finally:sys.argv=o
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase96_peer_benchmark_hard_data_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase96_pipeline"]
            self.assertEqual(d["mode"],"execute");self.assertGreater(d["records_loaded"],0)
        finally:sys.argv=o
    def test_no_pending(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase96_peer_benchmark_hard_data_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            p=json.loads(buf.getvalue())["phase96_pipeline"]
            self.assertEqual(p["pending_created"],0);self.assertFalse(p["mock_used"])
        finally:sys.argv=o

class TestPhase96Dashboard(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase96_peer_benchmark_hard_data_dashboard import main as dm
        o=sys.argv[:]
        try:
            sys.argv=["d.py","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase96");self.assertFalse(d["mock_used"])
        finally:sys.argv=o

if __name__=="__main__":
    unittest.main()
