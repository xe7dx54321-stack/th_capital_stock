import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

class TestPhase107Config(unittest.TestCase):
    def test_load(self):
        from smr_phase107_config import load_config
        self.assertEqual(load_config()["phase"],"phase107")
    def test_boundary_only(self):
        from smr_phase107_config import is_boundary_only
        self.assertTrue(is_boundary_only())
    def test_paper_disabled(self):
        from smr_phase107_config import is_paper_trading_enabled
        self.assertFalse(is_paper_trading_enabled())

class TestPhase107ConceptRegistry(unittest.TestCase):
    def test_registry(self):
        from smr_phase107_paper_concept_registry import build_paper_concept_registry
        r=build_paper_concept_registry()
        self.assertEqual(r["phase107_paper_concept_registry"]["total_concepts"],7)
        self.assertTrue(r["phase107_paper_concept_registry"]["all_execution_disabled"])

class TestPhase107StateTaxonomy(unittest.TestCase):
    def test_taxonomy(self):
        from smr_phase107_paper_state_taxonomy import build_paper_state_taxonomy
        r=build_paper_state_taxonomy()
        self.assertEqual(r["phase107_paper_state_taxonomy"]["current_state"],"boundary_defined")
        self.assertTrue(r["phase107_paper_state_taxonomy"]["current_cannot_execute"])
        self.assertFalse(r["phase107_paper_state_taxonomy"]["paper_execution_reachable"])

class TestPhase107ActionRegistry(unittest.TestCase):
    def test_actions(self):
        from smr_phase107_paper_action_registry import build_paper_action_registry
        r=build_paper_action_registry()
        self.assertTrue(r["phase107_paper_action_registry"]["no_execution_possible"])

class TestPhase107SignalBoundary(unittest.TestCase):
    def test_boundary(self):
        from smr_phase107_paper_signal_boundary import build_paper_signal_boundary
        r=build_paper_signal_boundary()
        self.assertTrue(r["phase107_paper_signal_boundary"]["execution_blocked"])
        self.assertTrue(r["phase107_paper_signal_boundary"]["cannot_create_order"])

class TestPhase107IntentBoundary(unittest.TestCase):
    def test_boundary(self):
        from smr_phase107_paper_intent_boundary import build_paper_intent_boundary
        r=build_paper_intent_boundary()
        self.assertTrue(r["phase107_paper_intent_boundary"]["execution_blocked"])

class TestPhase107OrderBoundary(unittest.TestCase):
    def test_boundary(self):
        from smr_phase107_paper_order_boundary import build_paper_order_boundary
        r=build_paper_order_boundary()
        self.assertTrue(r["phase107_paper_order_boundary"]["order_creation_forbidden"])
        self.assertTrue(r["phase107_paper_order_boundary"]["execution_blocked"])

class TestPhase107TradeBoundary(unittest.TestCase):
    def test_boundary(self):
        from smr_phase107_paper_trade_boundary import build_paper_trade_boundary
        r=build_paper_trade_boundary()
        self.assertTrue(r["phase107_paper_trade_boundary"]["trade_creation_forbidden"])

class TestPhase107PortfolioBoundary(unittest.TestCase):
    def test_boundary(self):
        from smr_phase107_paper_portfolio_boundary import build_paper_portfolio_boundary
        r=build_paper_portfolio_boundary()
        self.assertTrue(r["phase107_paper_portfolio_boundary"]["position_creation_forbidden"])

class TestPhase107PnlBoundary(unittest.TestCase):
    def test_boundary(self):
        from smr_phase107_paper_pnl_boundary import build_paper_pnl_boundary
        r=build_paper_pnl_boundary()
        self.assertTrue(r["phase107_paper_pnl_boundary"]["pnl_calculation_forbidden"])

class TestPhase107Checklist(unittest.TestCase):
    def test_checklist(self):
        from smr_phase107_paper_pre_paper_checklist import build_pre_paper_readiness_checklist
        r=build_pre_paper_readiness_checklist()
        self.assertFalse(r["phase107_pre_paper_readiness_checklist"]["ready_for_paper_execution"])

class TestPhase107DependencyMatrix(unittest.TestCase):
    def test_matrix(self):
        from smr_phase107_paper_boundary_dependency_matrix import build_paper_boundary_dependency_matrix
        r=build_paper_boundary_dependency_matrix()
        self.assertTrue(r["phase107_paper_boundary_dependency_matrix"]["no_execution_dependency_bypassed"])

class TestPhase107Simulation(unittest.TestCase):
    def test_sim(self):
        from smr_phase107_paper_no_order_simulation import run_paper_no_order_simulation
        r=run_paper_no_order_simulation()
        self.assertEqual(r["phase107_paper_no_order_simulation"]["violations"],0)
        self.assertTrue(r["phase107_paper_no_order_simulation"]["all_blocked"])

class TestPhase107ViolationClassifier(unittest.TestCase):
    def test_classifier(self):
        from smr_phase107_paper_violation_classifier import build_paper_violation_classifier
        r=build_paper_violation_classifier()
        self.assertTrue(r["phase107_paper_violation_classifier"]["no_order_created"])
        self.assertTrue(r["phase107_paper_violation_classifier"]["all_detected"])

class TestPhase107AuditSchema(unittest.TestCase):
    def test_audit(self):
        from smr_phase107_paper_audit_schema import build_paper_audit_schema
        r=build_paper_audit_schema()
        self.assertEqual(r["phase107_paper_audit_schema"]["readiness_status"],"ready")

class TestPhase107Scorecard(unittest.TestCase):
    def test_scorecard(self):
        from smr_phase107_paper_boundary_scorecard import build_paper_boundary_scorecard
        r=build_paper_boundary_scorecard()
        self.assertFalse(r["phase107_paper_boundary_scorecard"]["ready_for_paper_execution"])
        self.assertFalse(r["phase107_paper_boundary_scorecard"]["paper_order_created"])

class TestPhase107Report(unittest.TestCase):
    def test_report(self):
        from smr_phase107_paper_boundary_report import build_paper_boundary_report
        r=build_paper_boundary_report()
        self.assertEqual(r["phase107_paper_boundary_report"]["boundary_definition_status"],"complete")
        self.assertFalse(r["phase107_paper_boundary_report"]["paper_trading_enabled"])

class TestPhase107Guard(unittest.TestCase):
    def test_guard(self):
        from smr_phase107_paper_cannot_conclude_guard import run_paper_guard
        r=run_paper_guard()
        self.assertEqual(r["phase107_guard"]["overall"],"pass")
        self.assertEqual(r["phase107_guard"]["violations"],0)
        self.assertTrue(r["phase107_guard"]["paper_boundary_only"])

class TestPhase107Backlog(unittest.TestCase):
    def test_backlog(self):
        from smr_phase107_backlog_update import build_backlog_update
        r=build_backlog_update()
        self.assertTrue(r["phase107_backlog_update"]["phase107_status"]["paper_trading_boundary_defined"])
        self.assertEqual(r["phase107_backlog_update"]["phase107_status"]["paper_trading_boundary_missing"],"addressed")
        self.assertEqual(r["phase107_backlog_update"]["phase107_status"]["paper_order_execution_missing"],"unresolved")

class TestPhase107Dashboard(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase107_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase107")
            self.assertTrue(d["boundary_definition_only"])
            self.assertFalse(d["paper_trading_enabled"])
            self.assertFalse(d["ready_for_paper_execution"])
        finally:sys.argv=old

class TestPhase107Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase107_paper_trading_boundary import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase107_pipeline"]
            self.assertTrue(d["boundary_definition_only"])
            self.assertFalse(d["paper_trading_enabled"])
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase107_paper_trading_boundary import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase107_pipeline"]
            self.assertFalse(d["ready_for_paper_execution"])
            self.assertFalse(d["mock_used"]);self.assertFalse(d["fixture_used"])
        finally:sys.argv=old
    def test_skip_network(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase107_paper_trading_boundary import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase107_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertEqual(d["violations"],0)
        finally:sys.argv=old

if __name__=="__main__":
    unittest.main()
