import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

class TestPhase105Config(unittest.TestCase):
    def test_load(self):
        from smr_phase105_config import load_config
        self.assertEqual(load_config()["phase"],"phase105")
    def test_assessment_only(self):
        from smr_phase105_config import is_assessment_only
        self.assertTrue(is_assessment_only())
    def test_safe_mode(self):
        from smr_phase105_config import get_safe_mode
        sm=get_safe_mode()
        self.assertTrue(sm["disable_live"])
        self.assertTrue(sm["disable_order"])
        self.assertTrue(sm["disable_trade"])

class TestPhase105DomainRegistry(unittest.TestCase):
    def test_registry(self):
        from smr_phase105_emergency_domain_registry import build_emergency_domain_registry
        r=build_emergency_domain_registry()
        self.assertEqual(r["phase105_emergency_domain_registry"]["total_domains"],12)
        self.assertFalse(r["phase105_emergency_domain_registry"]["mock_used"])

class TestPhase105PolicyRegistry(unittest.TestCase):
    def test_registry(self):
        from smr_phase105_kill_switch_policy_registry import build_kill_switch_policy_registry
        r=build_kill_switch_policy_registry()
        self.assertEqual(r["phase105_kill_switch_policy_registry"]["total_policies"],9)
        self.assertFalse(r["phase105_kill_switch_policy_registry"]["fixture_used"])

class TestPhase105StateMachine(unittest.TestCase):
    def test_machine(self):
        from smr_phase105_emergency_stop_state_machine import build_emergency_stop_state_machine
        r=build_emergency_stop_state_machine()
        self.assertTrue(r["phase105_emergency_stop_state_machine"]["auto_resume_disabled"])
        self.assertEqual(r["phase105_emergency_stop_state_machine"]["total_transitions"],8)

class TestPhase105DisableLive(unittest.TestCase):
    def test_disable(self):
        from smr_phase105_disable_live_mode import build_disable_live_mode
        r=build_disable_live_mode()
        self.assertTrue(r["phase105_disable_live_mode"]["live_mode_disabled"])
        self.assertTrue(r["phase105_disable_live_mode"]["no_order_created"])
        self.assertTrue(r["phase105_disable_live_mode"]["no_broker_action"])

class TestPhase105DisableOrder(unittest.TestCase):
    def test_disable(self):
        from smr_phase105_disable_order_creation import build_disable_order_creation
        r=build_disable_order_creation()
        self.assertTrue(r["phase105_disable_order_creation"]["order_creation_disabled"])
        self.assertTrue(r["phase105_disable_order_creation"]["no_order_created"])

class TestPhase105SafeMode(unittest.TestCase):
    def test_safe_mode(self):
        from smr_phase105_safe_mode import build_safe_mode
        r=build_safe_mode()
        self.assertEqual(r["phase105_safe_mode"]["safe_mode_readiness"],"ready")
        self.assertTrue(r["phase105_safe_mode"]["auto_exit"]==False)
        self.assertTrue(r["phase105_safe_mode"]["no_order_created"])

class TestPhase105Rollback(unittest.TestCase):
    def test_manifest(self):
        from smr_phase105_rollback_manifest import build_rollback_manifest_schema
        r=build_rollback_manifest_schema()
        self.assertTrue(r["phase105_rollback_manifest_schema"]["schema"]["no_order_created"])
        self.assertIn("rollback_type",str(r["phase105_rollback_manifest_schema"]["schema"]))

class TestPhase105LastGoodState(unittest.TestCase):
    def test_registry(self):
        from smr_phase105_last_good_state import build_last_good_state_registry
        r=build_last_good_state_registry()
        self.assertEqual(r["phase105_last_good_state_registry"]["readiness_status"],"partial_ready")

class TestPhase105IncidentEscalation(unittest.TestCase):
    def test_escalation(self):
        from smr_phase105_incident_escalation import build_incident_escalation
        r=build_incident_escalation()
        self.assertEqual(len(r["phase105_incident_escalation"]["escalation_path"]),4)
        self.assertTrue(r["phase105_incident_escalation"]["no_order_created"])

class TestPhase105OverrideLockdown(unittest.TestCase):
    def test_lockdown(self):
        from smr_phase105_manual_override_lockdown import build_manual_override_lockdown
        r=build_manual_override_lockdown()
        self.assertTrue(r["phase105_manual_override_lockdown"]["override_lockdown_enabled"])
        self.assertIn("kill_switch",r["phase105_manual_override_lockdown"]["cannot_override"])

class TestPhase105AuditLog(unittest.TestCase):
    def test_audit(self):
        from smr_phase105_emergency_audit_log import build_emergency_audit_log_schema
        r=build_emergency_audit_log_schema()
        self.assertEqual(r["phase105_emergency_audit_log_schema"]["readiness_status"],"ready")

class TestPhase105Simulation(unittest.TestCase):
    def test_simulation(self):
        from smr_phase105_no_order_emergency_simulation import run_no_order_emergency_simulation
        r=run_no_order_emergency_simulation()
        self.assertEqual(r["phase105_no_order_emergency_simulation"]["violations"],0)
        self.assertTrue(r["phase105_no_order_emergency_simulation"]["no_order_created"])
        self.assertTrue(r["phase105_no_order_emergency_simulation"]["no_trade_created"])
        self.assertTrue(r["phase105_no_order_emergency_simulation"]["no_broker_action_taken"])
        self.assertTrue(r["phase105_no_order_emergency_simulation"]["no_position_sizing_created"])

class TestPhase105ViolationClassifier(unittest.TestCase):
    def test_classifier(self):
        from smr_phase105_emergency_violation_classifier import build_emergency_violation_classifier
        r=build_emergency_violation_classifier()
        self.assertTrue(r["phase105_emergency_violation_classifier"]["no_order_created"])
        self.assertTrue(r["phase105_emergency_violation_classifier"]["all_detected"])

class TestPhase105Scorecard(unittest.TestCase):
    def test_scorecard(self):
        from smr_phase105_emergency_readiness_scorecard import build_emergency_readiness_scorecard
        r=build_emergency_readiness_scorecard()
        self.assertEqual(r["phase105_emergency_readiness_scorecard"]["overall_readiness"],"partial_ready")
        self.assertFalse(r["phase105_emergency_readiness_scorecard"]["mock_used"])

class TestPhase105ReadinessReport(unittest.TestCase):
    def test_report(self):
        from smr_phase105_emergency_readiness_report import build_emergency_readiness_report
        r=build_emergency_readiness_report()
        self.assertEqual(r["phase105_emergency_readiness_report"]["kill_switch_readiness"],"partial_ready")
        self.assertTrue(r["phase105_emergency_readiness_report"]["no_order_created"])

class TestPhase105Guard(unittest.TestCase):
    def test_guard(self):
        from smr_phase105_emergency_cannot_conclude_guard import run_emergency_guard
        r=run_emergency_guard()
        self.assertEqual(r["phase105_guard"]["overall"],"pass")
        self.assertEqual(r["phase105_guard"]["violations"],0)
        self.assertTrue(r["phase105_guard"]["kill_switch_not_trade_signal"])

class TestPhase105Backlog(unittest.TestCase):
    def test_backlog(self):
        from smr_phase105_backlog_update import build_backlog_update
        r=build_backlog_update()
        self.assertEqual(r["phase105_backlog_update"]["phase101_blockers"]["kill_switch_missing"],"partially_addressed (Phase105)")
        self.assertTrue(r["phase105_backlog_update"]["phase105_status"]["phase101_all_blockers_addressed"])

class TestPhase105Dashboard(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase105_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase105")
            self.assertTrue(d["no_order_created"])
            self.assertEqual(d["pending_created"],0)
            self.assertEqual(d["paper_order_created"],0)
            self.assertEqual(d["target_price"],0)
            self.assertEqual(d["position_sizing"],0)
        finally:sys.argv=old

class TestPhase105Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase105_kill_switch_readiness import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase105_pipeline"]
            self.assertTrue(d["assessment_only"])
            self.assertFalse(d["kill_switch_execution_allowed"])
            self.assertTrue(d["no_order_created"])
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase105_kill_switch_readiness import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase105_pipeline"]
            self.assertEqual(d["pending_created"],0)
            self.assertEqual(d["paper_order_created"],0)
            self.assertEqual(d["real_trade_created"],0)
            self.assertEqual(d["target_price"],0)
            self.assertEqual(d["position_sizing"],0)
            self.assertFalse(d["mock_used"])
            self.assertFalse(d["fixture_used"])
        finally:sys.argv=old
    def test_skip_network(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase105_kill_switch_readiness import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase105_pipeline"]
            self.assertEqual(d["guard"],"pass")
            self.assertEqual(d["violations"],0)
        finally:sys.argv=old

if __name__=="__main__":
    unittest.main()
