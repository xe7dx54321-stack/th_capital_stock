import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

class TestPhase95Config(unittest.TestCase):
    def test_load(self):
        from smr_phase95_config import load_config
        self.assertEqual(load_config()["phase"],"phase95")
    def test_targets(self):
        from smr_phase95_config import load_config
        t=load_config()["targets"]
        self.assertIn("300394",t);self.assertIn("688041",t)
    def test_no_mock(self):
        from smr_phase95_config import load_config
        self.assertFalse(load_config()["safety"]["mock_allowed"])

class Test300394Resolver(unittest.TestCase):
    def test_dry_run(self):
        from smr_phase95_300394_resolver import resolve_300394
        r=resolve_300394("dry-run")
        d=r["phase95_300394_resolution"]
        self.assertEqual(d["mode"],"dry-run")
    def test_execute_has_fields(self):
        from smr_phase95_300394_resolver import resolve_300394
        r=resolve_300394("execute")
        d=r["phase95_300394_resolution"]
        self.assertIn("identity_found",d)
        self.assertIn("source_exhausted",d)
        self.assertIn("blocker_status",d)
        self.assertIn("allowed_next_action",d)
    def test_no_mock(self):
        from smr_phase95_300394_resolver import resolve_300394
        self.assertFalse(resolve_300394("execute")["phase95_300394_resolution"]["mock_used"])

class Test688041Valuation(unittest.TestCase):
    def test_dry_run(self):
        from smr_phase95_688041_valuation import harden_valuation
        r=harden_valuation("dry-run")
        self.assertEqual(r["phase95_688041_valuation"]["mode"],"dry-run")
    def test_execute_available(self):
        from smr_phase95_688041_valuation import harden_valuation
        r=harden_valuation("execute")
        d=r["phase95_688041_valuation"]
        self.assertIn(d.get("valuation_available"),["available","partial","unavailable"])
    def test_no_mock(self):
        from smr_phase95_688041_valuation import harden_valuation
        self.assertFalse(harden_valuation("execute")["phase95_688041_valuation"]["mock_used"])

class Test688041Pricing(unittest.TestCase):
    def test_execute_resolved(self):
        from smr_phase95_688041_pricing import harden_pricing
        r=harden_pricing("execute")
        self.assertTrue(r["phase95_688041_pricing"]["pricing_available"])
    def test_no_mock(self):
        from smr_phase95_688041_pricing import harden_pricing
        self.assertFalse(harden_pricing("execute")["phase95_688041_pricing"]["mock_used"])

class TestCoverageUpdate(unittest.TestCase):
    def test_build(self):
        from smr_phase95_300394_resolver import resolve_300394
        from smr_phase95_688041_valuation import harden_valuation
        from smr_phase95_688041_pricing import harden_pricing
        from smr_phase95_coverage_update import build_coverage
        r3=resolve_300394("execute");v6=harden_valuation("execute");p6=harden_pricing("execute")
        cm=build_coverage(r3,v6,p6)
        self.assertEqual(cm["phase95_coverage_update"]["covered"],6)
        self.assertEqual(cm["phase95_coverage_update"]["blocked"],1)
    def test_300394_blocked(self):
        from smr_phase95_300394_resolver import resolve_300394
        from smr_phase95_688041_valuation import harden_valuation
        from smr_phase95_688041_pricing import harden_pricing
        from smr_phase95_coverage_update import build_coverage
        r3=resolve_300394("execute");v6=harden_valuation("execute");p6=harden_pricing("execute")
        cm=build_coverage(r3,v6,p6)
        row=[r for r in cm["phase95_coverage_update"]["rows"] if r["ticker"]=="300394.SZ"][0]
        self.assertEqual(row["coverage"],"blocked")
    def test_688041_partial(self):
        from smr_phase95_300394_resolver import resolve_300394
        from smr_phase95_688041_valuation import harden_valuation
        from smr_phase95_688041_pricing import harden_pricing
        from smr_phase95_coverage_update import build_coverage
        r3=resolve_300394("execute");v6=harden_valuation("execute");p6=harden_pricing("execute")
        cm=build_coverage(r3,v6,p6)
        row=[r for r in cm["phase95_coverage_update"]["rows"] if r["ticker"]=="688041.SH"][0]
        self.assertEqual(row["coverage"],"partial")

class TestGapBacklog(unittest.TestCase):
    def test_closeout(self):
        from smr_phase95_300394_resolver import resolve_300394
        from smr_phase95_688041_valuation import harden_valuation
        from smr_phase95_688041_pricing import harden_pricing
        from smr_phase95_gap_backlog import build_gap_closeout
        r3=resolve_300394("execute");v6=harden_valuation("execute");p6=harden_pricing("execute")
        gc=build_gap_closeout(r3,v6,p6)
        self.assertEqual(gc["phase95_gap_closeout"]["still_blocked"],1)
    def test_backlog_phase96(self):
        from smr_phase95_gap_backlog import build_backlog
        bl=build_backlog()
        self.assertIn("peer_benchmark",bl["phase95_backlog"]["phase96_recommendation"])
    def test_backlog_items(self):
        from smr_phase95_gap_backlog import build_backlog
        bl=build_backlog()
        self.assertGreater(bl["phase95_backlog"]["items"],0)

class TestRunner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase95_gap_close_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())
            self.assertEqual(d["phase95_pipeline"]["mode"],"dry-run")
        finally:sys.argv=o
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase95_gap_close_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())
            p=d["phase95_pipeline"]
            self.assertEqual(p["mode"],"execute");self.assertEqual(p["tickers"],8)
        finally:sys.argv=o
    def test_no_pending(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase95_gap_close_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            p=json.loads(buf.getvalue())["phase95_pipeline"]
            self.assertEqual(p["pending_created"],0);self.assertFalse(p["mock_used"])
        finally:sys.argv=o

class TestDashboard(unittest.TestCase):
    def test_json(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase95_dashboard import main as dm
        o=sys.argv[:]
        try:
            sys.argv=["d.py","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())
            self.assertIn("300394_blocker",d["summary"])
        finally:sys.argv=o
    def test_no_mock(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase95_dashboard import main as dm
        o=sys.argv[:]
        try:
            sys.argv=["d.py","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())
            self.assertFalse(d["summary"]["mock_used"])
        finally:sys.argv=o

if __name__=="__main__":
    unittest.main()
