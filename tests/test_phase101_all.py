import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

class TestPhase101Config(unittest.TestCase):
    def test_load(self):
        from smr_phase101_config import load_config
        self.assertEqual(load_config()["phase"],"phase101")
    def test_assessment_only(self):
        from smr_phase101_config import is_assessment_only
        self.assertTrue(is_assessment_only())
    def test_live_disabled(self):
        from smr_phase101_config import is_live_trading_enabled
        self.assertFalse(is_live_trading_enabled())
    def test_domains(self):
        from smr_phase101_config import get_readiness_domains
        self.assertEqual(len(get_readiness_domains()),12)
    def test_no_mock(self):
        from smr_phase101_config import load_config
        self.assertFalse(load_config()["safety"]["mock_allowed"])

class TestPhase101DomainRegistry(unittest.TestCase):
    def test_registry(self):
        from smr_phase101_domain_registry import build_domain_registry
        r=build_domain_registry()
        self.assertEqual(r["phase101_domain_registry"]["total_domains"],12)

class TestPhase101Baseline(unittest.TestCase):
    def test_baseline(self):
        from smr_phase101_phase100_baseline import capture_phase100_baseline
        r=capture_phase100_baseline()
        self.assertEqual(r["phase101_baseline"]["production_status"],"pass")

class TestPhase101Scorecard(unittest.TestCase):
    def test_scorecard(self):
        from smr_phase101_scorecard import build_scorecard
        r=build_scorecard()
        self.assertEqual(r["phase101_scorecard"]["total_domains"],12)
        self.assertEqual(r["phase101_scorecard"]["overall_readiness"],"NOT_READY")
    def test_critical_blockers(self):
        from smr_phase101_scorecard import build_scorecard
        r=build_scorecard()
        self.assertGreater(len(r["phase101_scorecard"]["critical_blockers"]),2)

class TestPhase101GoNoGo(unittest.TestCase):
    def test_go_no_go(self):
        from smr_phase101_scorecard import build_scorecard
        from smr_phase101_go_no_go import build_go_no_go
        sc=build_scorecard();r=build_go_no_go(sc)
        self.assertEqual(r["phase101_go_no_go"]["decision"],"NO_GO")
        self.assertFalse(r["phase101_go_no_go"]["go_live_trading"])

class TestPhase101Markdown(unittest.TestCase):
    def test_markdown(self):
        from smr_phase101_scorecard import build_scorecard
        from smr_phase101_go_no_go import build_go_no_go
        from smr_phase101_markdown_report import build_markdown_report
        sc=build_scorecard();gg=build_go_no_go(sc);r=build_markdown_report(sc,gg)
        self.assertTrue(r["phase101_markdown_report"]["generated"])

class TestPhase101Assessments(unittest.TestCase):
    def test_all_12(self):
        modules=["data_source","hard_data_db","production_monitoring","evidence_signal","risk_control","paper_live","human_approval","execution_lockdown","audit_log","emergency_control","compliance_guardrail","system_stability"]
        for m in modules:
            mod=__import__(f"smr_phase101_{m}_readiness");fn=getattr(mod,f"assess_{m}_readiness")
            r=fn();self.assertIn("readiness_status",r[f"phase101_{m}_readiness"])

class TestPhase101Dashboard(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase101_dashboard import main as dm
        o=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase101");self.assertEqual(d["domains_assessed"],12)
            self.assertFalse(d["live_trading_enabled"]);self.assertFalse(d["go_live_trading"])
        finally:sys.argv=o

class TestPhase101Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase101_live_trading_readiness_assessment import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase101_pipeline"]
            self.assertEqual(d["mode"],"dry-run");self.assertEqual(d["go_no_go"],"NO_GO")
        finally:sys.argv=o
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase101_live_trading_readiness_assessment import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase101_pipeline"]
            self.assertEqual(d["mode"],"execute");self.assertEqual(d["go_live_trading"],False)
        finally:sys.argv=o
    def test_no_pending(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase101_live_trading_readiness_assessment import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            p=json.loads(buf.getvalue())["phase101_pipeline"]
            self.assertEqual(p["pending_created"],0);self.assertFalse(p["mock_used"])
        finally:sys.argv=o

if __name__=="__main__":
    unittest.main()
