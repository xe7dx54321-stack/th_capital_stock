import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

class TestPhase103Config(unittest.TestCase):
    def test_load(self):
        from smr_phase103_config import load_config
        self.assertEqual(load_config()["phase"],"phase103")
    def test_live_risk_disabled(self):
        from smr_phase103_config import is_live_risk_enabled
        self.assertFalse(is_live_risk_enabled())
    def test_seven_rules(self):
        from smr_phase103_config import get_risk_rules
        self.assertEqual(len(get_risk_rules()),7)

class TestPhase103Registry(unittest.TestCase):
    def test_registry(self):
        from smr_phase103_risk_rule_registry import build_risk_rule_registry
        r=build_risk_rule_registry()
        self.assertEqual(r["phase103_risk_rule_registry"]["total_rules"],7)

class TestPhase103Thresholds(unittest.TestCase):
    def test_thresholds(self):
        from smr_phase103_risk_threshold_config import build_risk_threshold_config
        r=build_risk_threshold_config()
        self.assertEqual(r["phase103_risk_thresholds"]["total_thresholds"],4)

class TestPhase103Checks(unittest.TestCase):
    def test_checks(self):
        from smr_phase103_risk_check_runner import run_risk_checks
        r=run_risk_checks()
        self.assertEqual(r["phase103_risk_checks"]["checks_fail"],0)
        self.assertTrue(r["phase103_risk_checks"]["no_orders_generated"])

class TestPhase103Audit(unittest.TestCase):
    def test_audit(self):
        from smr_phase103_risk_audit import build_risk_audit
        r=build_risk_audit()
        self.assertTrue(r["phase103_risk_audit"]["audit_complete"])

class TestPhase103QualityGate(unittest.TestCase):
    def test_gate(self):
        from smr_phase103_risk_rule_registry import build_risk_rule_registry
        from smr_phase103_risk_threshold_config import build_risk_threshold_config
        from smr_phase103_risk_check_runner import run_risk_checks
        from smr_phase103_risk_audit import build_risk_audit
        from smr_phase103_risk_quality_gate import run_risk_quality_gate
        reg=build_risk_rule_registry();th=build_risk_threshold_config()
        ck=run_risk_checks();au=build_risk_audit()
        r=run_risk_quality_gate(reg,th,ck,au)
        self.assertEqual(r["phase103_quality_gate"]["overall"],"pass")

class TestPhase103Guard(unittest.TestCase):
    def test_guard(self):
        from smr_phase103_risk_cannot_conclude_guard import run_risk_guard
        r=run_risk_guard()
        self.assertTrue(r["phase103_guard"]["no_position_sizing"])

class TestPhase103Dashboard(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase103_dashboard import main as dm
        o=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase103");self.assertFalse(d["live_risk_execution_enabled"])
            self.assertTrue(d["no_orders_generated"]);self.assertEqual(d["pending_created"],0)
        finally:sys.argv=o

class TestPhase103Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase103_risk_control_readiness import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase103_pipeline"]
            self.assertFalse(d["live_risk_execution_enabled"]);self.assertTrue(d["no_orders_generated"])
        finally:sys.argv=o
    def test_no_pending(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase103_risk_control_readiness import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            p=json.loads(buf.getvalue())["phase103_pipeline"]
            self.assertEqual(p["pending_created"],0);self.assertFalse(p["mock_used"])
        finally:sys.argv=o

if __name__=="__main__":
    unittest.main()
