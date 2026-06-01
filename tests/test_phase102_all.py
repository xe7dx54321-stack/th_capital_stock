import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

class TestPhase102Config(unittest.TestCase):
    def test_load(self):
        from smr_phase102_config import load_config
        self.assertEqual(load_config()["phase"],"phase102")
    def test_assessment_only(self):
        from smr_phase102_config import is_assessment_only
        self.assertTrue(is_assessment_only())
    def test_pnl_backtest_disabled(self):
        from smr_phase102_config import is_pnl_backtest_allowed
        self.assertFalse(is_pnl_backtest_allowed())
    def test_no_mock(self):
        from smr_phase102_config import load_config
        self.assertFalse(load_config()["safety"]["mock_allowed"])

class TestPhase102DBIntegrity(unittest.TestCase):
    def test_integrity(self):
        from smr_phase102_historical_db_integrity import check_historical_db_integrity
        r=check_historical_db_integrity()
        self.assertEqual(r["phase102_db_integrity"]["integrity_issues"],0)

class TestPhase102Coverage(unittest.TestCase):
    def test_coverage(self):
        from smr_phase102_historical_coverage import check_historical_coverage
        r=check_historical_coverage()
        self.assertEqual(r["phase102_historical_coverage"]["tickers_checked"],8)
        self.assertGreater(r["phase102_historical_coverage"]["coverage_pct"],50)

class TestPhase102ReplayRegistry(unittest.TestCase):
    def test_registry(self):
        from smr_phase102_replay_period_registry import build_replay_registry
        r=build_replay_registry()
        self.assertGreaterEqual(r["phase102_replay_registry"]["total_periods"],3)

class TestPhase102SignalValidator(unittest.TestCase):
    def test_validator(self):
        from smr_phase102_backtest_signal_validator import validate_backtest_signals
        r=validate_backtest_signals()
        self.assertGreater(r["phase102_signal_validator"]["tickers_pass"],3)
        self.assertFalse(r["phase102_signal_validator"]["pnl_backtest_attempted"])

class TestPhase102QualityGate(unittest.TestCase):
    def test_gate(self):
        from smr_phase102_historical_db_integrity import check_historical_db_integrity
        from smr_phase102_historical_coverage import check_historical_coverage
        from smr_phase102_backtest_signal_validator import validate_backtest_signals
        from smr_phase102_backtest_quality_gate import run_backtest_quality_gate
        di=check_historical_db_integrity();cv=check_historical_coverage();sv=validate_backtest_signals()
        r=run_backtest_quality_gate(di,cv,sv)
        self.assertEqual(r["phase102_quality_gate"]["overall"],"pass")

class TestPhase102Guard(unittest.TestCase):
    def test_guard(self):
        from smr_phase102_backtest_cannot_conclude_guard import run_backtest_guard
        r=run_backtest_guard()
        self.assertTrue(r["phase102_guard"]["pnl_backtest_forbidden_reminder"])
        self.assertTrue(r["phase102_guard"]["no_trade_signal_guaranteed"])

class TestPhase102Dashboard(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase102_dashboard import main as dm
        o=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase102");self.assertFalse(d["pnl_backtest_allowed"])
            self.assertFalse(d["mock_used"]);self.assertEqual(d["pending_created"],0)
        finally:sys.argv=o

class TestPhase102Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase102_backtest_readiness import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase102_pipeline"]
            self.assertEqual(d["mode"],"dry-run");self.assertFalse(d["pnl_backtest_allowed"])
        finally:sys.argv=o
    def test_no_pending(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase102_backtest_readiness import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            p=json.loads(buf.getvalue())["phase102_pipeline"]
            self.assertEqual(p["pending_created"],0);self.assertFalse(p["mock_used"])
        finally:sys.argv=o

if __name__=="__main__":
    unittest.main()
