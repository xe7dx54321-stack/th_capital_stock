import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

class TestPhase100Config(unittest.TestCase):
    def test_load(self):
        from smr_phase100_config import load_config
        self.assertEqual(load_config()["phase"],"phase100")
    def test_pipeline_order(self):
        from smr_phase100_config import get_pipeline_order
        self.assertEqual(len(get_pipeline_order()),3)
    def test_reports_gitignored(self):
        from smr_phase100_config import is_reports_gitignored
        self.assertTrue(is_reports_gitignored())
    def test_no_mock(self):
        from smr_phase100_config import load_config
        self.assertFalse(load_config()["safety"]["mock_allowed"])

class TestPhase100ExceptionBlocker(unittest.TestCase):
    def test_exceptions(self):
        from smr_phase100_exception_blocker import build_exception_blocker_report
        r=build_exception_blocker_report({"phase98_pipeline":{"sources_monitored":7}})
        self.assertEqual(r["phase100_exception_blocker"]["total_exceptions"],4)

class TestPhase100QualityGate(unittest.TestCase):
    def test_gate(self):
        from smr_phase100_quality_gate import run_production_quality_gate
        r=run_production_quality_gate()
        self.assertEqual(r["phase100_quality_gate"]["overall"],"pass")

class TestPhase100Guard(unittest.TestCase):
    def test_guard_clean(self):
        from smr_phase100_cannot_conclude_guard import run_production_guard
        r=run_production_guard({"phase100_operator_summary":{"markdown":"production status report"}})
        self.assertEqual(r["phase100_guard"]["overall"],"pass")
        self.assertEqual(r["phase100_guard"]["violations"],0)

class TestPhase100Backlog(unittest.TestCase):
    def test_backlog(self):
        from smr_phase100_backlog_update import build_backlog_update
        r=build_backlog_update()
        self.assertGreaterEqual(r["phase100_backlog_update"]["items"],6)
    def test_phase101(self):
        from smr_phase100_backlog_update import build_backlog_update
        self.assertIn("phase101_recommendation",build_backlog_update()["phase100_backlog_update"])

class TestPhase100Dashboard(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase100_dashboard import main as dm
        o=sys.argv[:]
        try:
            sys.argv=["d.py","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase100")
            self.assertFalse(d["mock_used"])
            self.assertEqual(d["pending_created"],0)
        finally:sys.argv=o

class TestPhase100Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase100_continuous_production_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase100_pipeline"]
            self.assertEqual(d["mode"],"dry-run")
            self.assertEqual(d["production_status"],"pass")
        finally:sys.argv=o
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase100_continuous_production_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase100_pipeline"]
            self.assertEqual(d["mode"],"execute")
            self.assertEqual(d["quality_gate"],"pass")
        finally:sys.argv=o
    def test_no_pending(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase100_continuous_production_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            p=json.loads(buf.getvalue())["phase100_pipeline"]
            self.assertEqual(p["pending_created"],0)
            self.assertFalse(p["mock_used"])
        finally:sys.argv=o

if __name__=="__main__":
    unittest.main()
