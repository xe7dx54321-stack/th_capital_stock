import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

class TestPhase106Config(unittest.TestCase):
    def test_load(self):
        from smr_phase106_config import load_config
        self.assertEqual(load_config()["phase"],"phase106")
    def test_assessment_only(self):
        from smr_phase106_config import is_assessment_only
        self.assertTrue(is_assessment_only())
    def test_modules(self):
        from smr_phase106_config import get_modules
        self.assertEqual(len(get_modules()),4)

class TestPhase106ModuleRegistry(unittest.TestCase):
    def test_registry(self):
        from smr_phase106_readiness_module_registry import build_readiness_module_registry
        r=build_readiness_module_registry()
        self.assertEqual(r["phase106_readiness_module_registry"]["total_modules"],4)
        self.assertTrue(r["phase106_readiness_module_registry"]["all_no_order"])
        self.assertFalse(r["phase106_readiness_module_registry"]["mock_used"])

class TestPhase106PhaseStatusLoader(unittest.TestCase):
    def test_loader(self):
        from smr_phase106_phase_status_loader import load_all_phase_status
        r=load_all_phase_status()
        self.assertTrue(r["phase106_phase_status_loader"]["phases_loaded"]>=0)

class TestPhase106DependencyRegistry(unittest.TestCase):
    def test_deps(self):
        from smr_phase106_cross_gate_dependency_registry import build_cross_gate_dependency_registry
        r=build_cross_gate_dependency_registry()
        self.assertEqual(r["phase106_cross_gate_dependency_registry"]["total_dependencies"],9)
        self.assertTrue(r["phase106_cross_gate_dependency_registry"]["all_no_order"])

class TestPhase106BlockerPropagation(unittest.TestCase):
    def test_propagation(self):
        from smr_phase106_blocker_propagation_checker import run_blocker_propagation_checker
        r=run_blocker_propagation_checker()
        self.assertTrue(r["phase106_blocker_propagation_checker"]["propagation_healthy"])
        self.assertEqual(r["phase106_blocker_propagation_checker"]["inconsistent"],0)

class TestPhase106StatusConsistency(unittest.TestCase):
    def test_consistency(self):
        from smr_phase106_readiness_status_consistency import run_readiness_status_consistency
        r=run_readiness_status_consistency()
        self.assertTrue(r["phase106_readiness_status_consistency"]["all_consistent"])

class TestPhase106NoOrderSafety(unittest.TestCase):
    def test_safety(self):
        from smr_phase106_no_order_safety_consistency import run_no_order_safety_consistency
        r=run_no_order_safety_consistency()
        self.assertTrue(r["phase106_no_order_safety_consistency"]["safety_boundary_intact"])
        self.assertEqual(r["phase106_no_order_safety_consistency"]["inconsistent"],0)

class TestPhase106GuardConsistency(unittest.TestCase):
    def test_guard(self):
        from smr_phase106_guard_consistency import run_guard_consistency
        r=run_guard_consistency()
        self.assertTrue(r["phase106_guard_consistency"]["all_guards_consistent"])

class TestPhase106DashboardConsistency(unittest.TestCase):
    def test_dash(self):
        from smr_phase106_dashboard_consistency import run_dashboard_consistency
        r=run_dashboard_consistency()
        self.assertTrue(r["phase106_dashboard_consistency"]["all_dashboards_consistent"])

class TestPhase106BacklogConsistency(unittest.TestCase):
    def test_backlog(self):
        from smr_phase106_backlog_consistency import run_backlog_consistency
        r=run_backlog_consistency()
        self.assertTrue(r["phase106_backlog_consistency"]["all_backlogs_consistent"])

class TestPhase106Simulation(unittest.TestCase):
    def test_sim(self):
        from smr_phase106_cross_gate_simulation import run_cross_gate_simulation
        r=run_cross_gate_simulation()
        self.assertEqual(r["phase106_cross_gate_simulation"]["violations"],0)
        self.assertTrue(r["phase106_cross_gate_simulation"]["all_scenarios_pass"])
        self.assertTrue(r["phase106_cross_gate_simulation"]["no_order_created"])
        self.assertTrue(r["phase106_cross_gate_simulation"]["no_trade_created"])

class TestPhase106ViolationClassifier(unittest.TestCase):
    def test_classifier(self):
        from smr_phase106_integration_violation_classifier import build_integration_violation_classifier
        r=build_integration_violation_classifier()
        self.assertTrue(r["phase106_integration_violation_classifier"]["no_order_created"])
        self.assertTrue(r["phase106_integration_violation_classifier"]["all_detected"])

class TestPhase106Scorecard(unittest.TestCase):
    def test_scorecard(self):
        from smr_phase106_integrated_readiness_scorecard import build_integrated_readiness_scorecard
        r=build_integrated_readiness_scorecard()
        self.assertEqual(r["phase106_integrated_readiness_scorecard"]["integrated_readiness"],"partial_ready")
        self.assertTrue(r["phase106_integrated_readiness_scorecard"]["no_module_trading_ready"])

class TestPhase106IntegrationReport(unittest.TestCase):
    def test_report(self):
        from smr_phase106_readiness_integration_report import build_readiness_integration_report
        r=build_readiness_integration_report()
        self.assertEqual(r["phase106_readiness_integration_report"]["integration_readiness"],"partial_ready")
        self.assertTrue(r["phase106_readiness_integration_report"]["no_order_created"])

class TestPhase106QualityGate(unittest.TestCase):
    def test_gate(self):
        from smr_phase106_blocker_propagation_checker import run_blocker_propagation_checker
        from smr_phase106_readiness_status_consistency import run_readiness_status_consistency
        from smr_phase106_no_order_safety_consistency import run_no_order_safety_consistency
        from smr_phase106_guard_consistency import run_guard_consistency
        from smr_phase106_dashboard_consistency import run_dashboard_consistency
        from smr_phase106_backlog_consistency import run_backlog_consistency
        from smr_phase106_cross_gate_simulation import run_cross_gate_simulation
        from smr_phase106_integration_quality_gate import run_integration_quality_gate
        bp=run_blocker_propagation_checker();rs=run_readiness_status_consistency()
        ns=run_no_order_safety_consistency();gc=run_guard_consistency()
        dc=run_dashboard_consistency();bl=run_backlog_consistency();sim=run_cross_gate_simulation()
        r=run_integration_quality_gate(bp,rs,ns,gc,dc,bl,sim)
        self.assertEqual(r["phase106_integration_quality_gate"]["overall"],"pass")

class TestPhase106Guard(unittest.TestCase):
    def test_guard(self):
        from smr_phase106_integration_cannot_conclude_guard import run_integration_guard
        r=run_integration_guard()
        self.assertEqual(r["phase106_guard"]["overall"],"pass")
        self.assertEqual(r["phase106_guard"]["violations"],0)
        self.assertTrue(r["phase106_guard"]["integration_not_trading_ready"])

class TestPhase106Backlog(unittest.TestCase):
    def test_backlog(self):
        from smr_phase106_backlog_update import build_backlog_update
        r=build_backlog_update()
        self.assertTrue(r["phase106_backlog_update"]["phase106_status"]["integration_readiness"]=="partial_ready")
        self.assertTrue(r["phase106_backlog_update"]["phase106_status"]["cross_gate_consistent"])

class TestPhase106Dashboard(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase106_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase106")
            self.assertTrue(d["integration_test_only"])
            self.assertFalse(d["paper_trading_enabled"])
            self.assertTrue(d["no_order_created"])
            self.assertEqual(d["pending_created"],0)
            self.assertEqual(d["target_price"],0)
        finally:sys.argv=old

class TestPhase106Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase106_readiness_integration import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase106_pipeline"]
            self.assertTrue(d["integration_test_only"])
            self.assertTrue(d["no_order_created"])
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase106_readiness_integration import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase106_pipeline"]
            self.assertEqual(d["pending_created"],0);self.assertEqual(d["paper_order_created"],0)
            self.assertFalse(d["mock_used"]);self.assertFalse(d["fixture_used"])
        finally:sys.argv=old
    def test_skip_network(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase106_readiness_integration import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase106_pipeline"]
            self.assertEqual(d["guard"],"pass")
            self.assertEqual(d["violations"],0)
        finally:sys.argv=old

if __name__=="__main__":
    unittest.main()
