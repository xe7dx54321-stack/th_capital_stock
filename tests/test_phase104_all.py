import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

class TestPhase104Config(unittest.TestCase):
    def test_load(self):
        from smr_phase104_config import load_config
        self.assertEqual(load_config()["phase"],"phase104")
    def test_assessment_only(self):
        from smr_phase104_config import is_assessment_only
        self.assertTrue(is_assessment_only())
    def test_policies_exist(self):
        from smr_phase104_config import get_approval_policies
        self.assertTrue(get_approval_policies()["two_step_required"])

class TestPhase104DomainRegistry(unittest.TestCase):
    def test_registry(self):
        from smr_phase104_approval_domain_registry import build_approval_domain_registry
        r=build_approval_domain_registry()
        self.assertEqual(r["phase104_approval_domain_registry"]["total_domains"],12)
        self.assertFalse(r["phase104_approval_domain_registry"]["mock_used"])

class TestPhase104PolicyRegistry(unittest.TestCase):
    def test_registry(self):
        from smr_phase104_approval_policy_registry import build_approval_policy_registry
        r=build_approval_policy_registry()
        self.assertEqual(r["phase104_approval_policy_registry"]["total_policies"],9)
        self.assertFalse(r["phase104_approval_policy_registry"]["fixture_used"])

class TestPhase104StateMachine(unittest.TestCase):
    def test_machine(self):
        from smr_phase104_approval_state_machine import build_approval_state_machine
        r=build_approval_state_machine()
        self.assertTrue(r["phase104_approval_state_machine"]["two_step_enforced"])
        self.assertEqual(r["phase104_approval_state_machine"]["total_transitions"],8)

class TestPhase104RequestSchema(unittest.TestCase):
    def test_schema(self):
        from smr_phase104_approval_request_schema import build_approval_request_schema
        r=build_approval_request_schema()
        self.assertTrue(r["phase104_approval_request_schema"]["no_order_creation"])
        self.assertTrue(r["phase104_approval_request_schema"]["no_trade_creation"])

class TestPhase104DecisionSchema(unittest.TestCase):
    def test_schema(self):
        from smr_phase104_approval_decision_schema import build_approval_decision_schema
        r=build_approval_decision_schema()
        self.assertTrue(r["phase104_approval_decision_schema"]["no_order_creation"])
        self.assertTrue(r["phase104_approval_decision_schema"]["no_trade_creation"])

class TestPhase104TwoStep(unittest.TestCase):
    def test_two_step(self):
        from smr_phase104_two_step_approval import build_two_step_approval
        r=build_two_step_approval()
        self.assertTrue(r["phase104_two_step_approval"]["no_order_created"])
        self.assertTrue(r["phase104_two_step_approval"]["no_trade_created"])

class TestPhase104Expiration(unittest.TestCase):
    def test_expiration(self):
        from smr_phase104_approval_expiration import build_approval_expiration
        r=build_approval_expiration()
        self.assertEqual(r["phase104_approval_expiration"]["readiness_status"],"ready")
        self.assertTrue(r["phase104_approval_expiration"]["no_order_created"])

class TestPhase104Revocation(unittest.TestCase):
    def test_revocation(self):
        from smr_phase104_approval_revocation import build_approval_revocation
        r=build_approval_revocation()
        self.assertEqual(r["phase104_approval_revocation"]["readiness_status"],"partial_ready")
        self.assertTrue(r["phase104_approval_revocation"]["no_order_created"])

class TestPhase104OperatorIdentity(unittest.TestCase):
    def test_identity(self):
        from smr_phase104_operator_identity import build_operator_identity
        r=build_operator_identity()
        self.assertEqual(r["phase104_operator_identity"]["readiness_status"],"not_ready")
        self.assertTrue(len(r["phase104_operator_identity"]["blockers"])>0)

class TestPhase104AuditLog(unittest.TestCase):
    def test_audit(self):
        from smr_phase104_approval_audit_log import build_approval_audit_log_schema
        r=build_approval_audit_log_schema()
        self.assertEqual(r["phase104_approval_audit_log_schema"]["readiness_status"],"ready")

class TestPhase104ManualOverride(unittest.TestCase):
    def test_override(self):
        from smr_phase104_manual_override import build_manual_override
        r=build_manual_override()
        self.assertTrue(r["phase104_manual_override"]["requires_supervisor"])
        self.assertTrue(r["phase104_manual_override"]["no_order_created"])

class TestPhase104Simulation(unittest.TestCase):
    def test_simulation(self):
        from smr_phase104_no_order_approval_simulation import run_no_order_approval_simulation
        r=run_no_order_approval_simulation()
        self.assertEqual(r["phase104_no_order_approval_simulation"]["violations"],0)
        self.assertTrue(r["phase104_no_order_approval_simulation"]["no_order_created"])
        self.assertTrue(r["phase104_no_order_approval_simulation"]["no_trade_created"])
        self.assertTrue(r["phase104_no_order_approval_simulation"]["no_position_sizing_created"])

class TestPhase104ViolationClassifier(unittest.TestCase):
    def test_classifier(self):
        from smr_phase104_approval_violation_classifier import build_approval_violation_classifier
        r=build_approval_violation_classifier()
        self.assertTrue(r["phase104_approval_violation_classifier"]["no_order_created"])
        self.assertTrue(r["phase104_approval_violation_classifier"]["all_detected"])

class TestPhase104Scorecard(unittest.TestCase):
    def test_scorecard(self):
        from smr_phase104_approval_readiness_scorecard import build_approval_readiness_scorecard
        r=build_approval_readiness_scorecard()
        self.assertEqual(r["phase104_approval_readiness_scorecard"]["overall_readiness"],"partial_ready")
        self.assertFalse(r["phase104_approval_readiness_scorecard"]["mock_used"])

class TestPhase104ReadinessReport(unittest.TestCase):
    def test_report(self):
        from smr_phase104_approval_readiness_report import build_approval_readiness_report
        r=build_approval_readiness_report()
        self.assertEqual(r["phase104_approval_readiness_report"]["human_approval_readiness"],"partial_ready")
        self.assertTrue(r["phase104_approval_readiness_report"]["no_order_created"])

class TestPhase104Guard(unittest.TestCase):
    def test_guard(self):
        from smr_phase104_approval_cannot_conclude_guard import run_approval_guard
        r=run_approval_guard()
        self.assertEqual(r["phase104_guard"]["overall"],"pass")
        self.assertEqual(r["phase104_guard"]["violations"],0)
        self.assertTrue(r["phase104_guard"]["human_approval_not_trade_signal"])

class TestPhase104Backlog(unittest.TestCase):
    def test_backlog(self):
        from smr_phase104_backlog_update import build_backlog_update
        r=build_backlog_update()
        self.assertEqual(r["phase104_backlog_update"]["phase101_blockers"]["human_approval_missing"],"partially_addressed (Phase104)")
        self.assertEqual(r["phase104_backlog_update"]["phase101_blockers"]["kill_switch_missing"],"unresolved")

class TestPhase104Dashboard(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase104_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase104")
            self.assertTrue(d["no_order_created"])
            self.assertEqual(d["pending_created"],0)
            self.assertEqual(d["paper_order_created"],0)
            self.assertEqual(d["real_trade_created"],0)
            self.assertEqual(d["target_price"],0)
            self.assertEqual(d["position_sizing"],0)
        finally:sys.argv=old

class TestPhase104Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase104_human_approval_readiness import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase104_pipeline"]
            self.assertTrue(d["assessment_only"])
            self.assertFalse(d["approval_execution_allowed"])
            self.assertTrue(d["no_order_created"])
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase104_human_approval_readiness import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase104_pipeline"]
            self.assertEqual(d["pending_created"],0)
            self.assertEqual(d["paper_order_created"],0)
            self.assertEqual(d["real_trade_created"],0)
            self.assertEqual(d["target_price"],0)
            self.assertEqual(d["position_sizing"],0)
            self.assertFalse(d["mock_used"])
            self.assertFalse(d["fixture_used"])
            self.assertFalse(d["raw_saved"])
        finally:sys.argv=old
    def test_skip_network(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase104_human_approval_readiness import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase104_pipeline"]
            self.assertEqual(d["guard"],"pass")
            self.assertEqual(d["violations"],0)
        finally:sys.argv=old

if __name__=="__main__":
    unittest.main()
