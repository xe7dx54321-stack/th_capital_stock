import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
class TestPhase108Config(unittest.TestCase):
    def test_load(self):
        from smr_phase108_config import load_config
        self.assertEqual(load_config()["phase"],"phase108")
    def test_readiness_only(self):
        from smr_phase108_config import is_readiness_only
        self.assertTrue(is_readiness_only())
    def test_execution_disabled(self):
        from smr_phase108_config import is_paper_execution_enabled
        self.assertFalse(is_paper_execution_enabled())
class TestPhase108DomainRegistry(unittest.TestCase):
    def test_domains(self):
        from smr_phase108_readiness_domain_registry import build_readiness_domain_registry
        r=build_readiness_domain_registry()
        self.assertEqual(r["phase108_readiness_domain_registry"]["total_domains"],12)
        self.assertTrue(r["phase108_readiness_domain_registry"]["all_execution_disabled"])
class TestPhase108Checklist(unittest.TestCase):
    def test_checklist(self):
        from smr_phase108_pre_paper_checklist import build_pre_paper_checklist
        r=build_pre_paper_checklist()
        self.assertFalse(r["phase108_pre_paper_checklist"]["ready_for_paper_execution"])
        self.assertEqual(r["phase108_pre_paper_checklist"]["blockers"],4)
class TestPhase108SchemaReviews(unittest.TestCase):
    def test_order(self):
        from smr_phase108_paper_order_schema_review import build_paper_order_schema_review
        r=build_paper_order_schema_review()
        self.assertEqual(r["phase108_paper_order_schema_review"]["review_status"],"pass")
    def test_trade(self):
        from smr_phase108_paper_trade_schema_review import build_paper_trade_schema_review
        r=build_paper_trade_schema_review()
        self.assertEqual(r["phase108_paper_trade_schema_review"]["review_status"],"pass")
    def test_portfolio(self):
        from smr_phase108_paper_portfolio_schema_review import build_paper_portfolio_schema_review
        r=build_paper_portfolio_schema_review()
        self.assertEqual(r["phase108_paper_portfolio_schema_review"]["review_status"],"pass")
class TestPhase108PnlPolicy(unittest.TestCase):
    def test_pnl(self):
        from smr_phase108_paper_pnl_policy_readiness import build_paper_pnl_policy_readiness
        r=build_paper_pnl_policy_readiness()
        self.assertEqual(r["phase108_paper_pnl_policy_readiness"]["readiness_status"],"partial_ready")
        self.assertFalse(r["phase108_paper_pnl_policy_readiness"]["pnl_calculation_allowed"])
class TestPhase108SizingPolicy(unittest.TestCase):
    def test_sizing(self):
        from smr_phase108_paper_sizing_policy_readiness import build_paper_sizing_policy_readiness
        r=build_paper_sizing_policy_readiness()
        self.assertFalse(r["phase108_paper_sizing_policy_readiness"]["position_sizing_allowed"])
class TestPhase108Dependencies(unittest.TestCase):
    def test_operator(self):
        from smr_phase108_operator_identity_dependency import build_operator_identity_dependency
        r=build_operator_identity_dependency()
        self.assertFalse(r["phase108_operator_identity_dependency"]["ready_for_execution"])
        self.assertTrue(r["phase108_operator_identity_dependency"]["blocker"])
    def test_approval(self):
        from smr_phase108_approval_dependency import build_approval_dependency
        r=build_approval_dependency()
        self.assertFalse(r["phase108_approval_dependency"]["ready_for_execution"])
    def test_risk(self):
        from smr_phase108_risk_dependency import build_risk_dependency
        r=build_risk_dependency()
        self.assertFalse(r["phase108_risk_dependency"]["ready_for_execution"])
    def test_kill_switch(self):
        from smr_phase108_kill_switch_dependency import build_kill_switch_dependency
        r=build_kill_switch_dependency()
        self.assertFalse(r["phase108_kill_switch_dependency"]["ready_for_execution"])
class TestPhase108SafetyGate(unittest.TestCase):
    def test_gate(self):
        from smr_phase108_safety_gate import run_safety_gate
        r=run_safety_gate()
        self.assertEqual(r["phase108_safety_gate"]["overall"],"pass")
        self.assertTrue(r["phase108_safety_gate"]["all_execution_disabled"])
class TestPhase108DisabledVerifier(unittest.TestCase):
    def test_disabled(self):
        from smr_phase108_disabled_state_verifier import run_disabled_state_verifier
        r=run_disabled_state_verifier()
        self.assertTrue(r["phase108_disabled_state_verifier"]["all_disabled"])
class TestPhase108Simulation(unittest.TestCase):
    def test_sim(self):
        from smr_phase108_dry_run_simulation import run_dry_run_simulation
        r=run_dry_run_simulation()
        self.assertEqual(r["phase108_dry_run_simulation"]["violations"],0)
        self.assertTrue(r["phase108_dry_run_simulation"]["all_disabled_verified"])
class TestPhase108ViolationClassifier(unittest.TestCase):
    def test_vc(self):
        from smr_phase108_violation_classifier import build_violation_classifier
        r=build_violation_classifier()
        self.assertTrue(r["phase108_violation_classifier"]["no_order_created"])
class TestPhase108Scorecard(unittest.TestCase):
    def test_sc(self):
        from smr_phase108_readiness_scorecard import build_readiness_scorecard
        r=build_readiness_scorecard()
        self.assertFalse(r["phase108_readiness_scorecard"]["ready_for_paper_execution"])
class TestPhase108Report(unittest.TestCase):
    def test_rpt(self):
        from smr_phase108_readiness_report import build_readiness_report
        r=build_readiness_report()
        self.assertEqual(r["phase108_readiness_report"]["paper_execution_readiness"],"partial_ready")
        self.assertFalse(r["phase108_readiness_report"]["paper_execution_enabled"])
class TestPhase108Guard(unittest.TestCase):
    def test_guard(self):
        from smr_phase108_cannot_conclude_guard import run_guard
        r=run_guard()
        self.assertEqual(r["phase108_guard"]["overall"],"pass")
        self.assertEqual(r["phase108_guard"]["violations"],0)
        self.assertTrue(r["phase108_guard"]["paper_execution_not_ready"])
class TestPhase108Backlog(unittest.TestCase):
    def test_bl(self):
        from smr_phase108_backlog_update import build_backlog_update
        r=build_backlog_update()
        self.assertFalse(r["phase108_backlog_update"]["phase108_status"]["ready_for_paper_execution"])
class TestPhase108Dashboard(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase108_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase108");self.assertTrue(d["readiness_only"])
            self.assertFalse(d["paper_execution_enabled"]);self.assertFalse(d["ready_for_paper_execution"])
        finally:sys.argv=old
class TestPhase108Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase108_paper_execution_readiness import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase108_pipeline"]
            self.assertTrue(d["readiness_only"]);self.assertFalse(d["paper_execution_enabled"])
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase108_paper_execution_readiness import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase108_pipeline"]
            self.assertFalse(d["ready_for_paper_execution"]);self.assertFalse(d["mock_used"])
        finally:sys.argv=old
    def test_skip(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase108_paper_execution_readiness import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase108_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertEqual(d["violations"],0)
        finally:sys.argv=old
if __name__=="__main__":unittest.main()
