import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
class T109Config(unittest.TestCase):
    def test_load(self):
        from smr_phase109_config import load_config
        self.assertEqual(load_config()["phase"],"phase109")
    def test_identity_only(self):
        from smr_phase109_config import is_identity_readiness_only
        self.assertTrue(is_identity_readiness_only())
    def test_no_accounts(self):
        from smr_phase109_config import is_account_creation_allowed
        self.assertFalse(is_account_creation_allowed())
class T109DomainRegistry(unittest.TestCase):
    def test_domains(self):
        from smr_phase109_identity_domain_registry import build_identity_domain_registry
        r=build_identity_domain_registry()
        self.assertEqual(r["phase109_identity_domain_registry"]["total_domains"],12)
        self.assertFalse(r["phase109_identity_domain_registry"]["all_provisioned"])
class T109IdentitySchema(unittest.TestCase):
    def test_schema(self):
        from smr_phase109_operator_identity_schema import build_operator_identity_schema
        r=build_operator_identity_schema()
        self.assertEqual(r["phase109_operator_identity_schema"]["account_created"],0)
        self.assertEqual(r["phase109_operator_identity_schema"]["sso_connected"],0)
class T109RoleRegistry(unittest.TestCase):
    def test_roles(self):
        from smr_phase109_operator_role_registry import build_operator_role_registry
        r=build_operator_role_registry()
        self.assertEqual(r["phase109_operator_role_registry"]["total_roles"],5)
        self.assertTrue(r["phase109_operator_role_registry"]["all_order_creation_disabled"])
class T109PermissionMatrix(unittest.TestCase):
    def test_matrix(self):
        from smr_phase109_permission_matrix import build_permission_matrix
        r=build_permission_matrix()
        self.assertTrue(r["phase109_permission_matrix"]["matrix"]["all_execution_permissions_disabled"])
class T109ApprovalBinding(unittest.TestCase):
    def test_binding(self):
        from smr_phase109_approval_role_binding import build_approval_role_binding
        r=build_approval_role_binding()
        self.assertTrue(r["phase109_approval_role_binding"]["same_person_forbidden"])
class T109SupervisorIdentity(unittest.TestCase):
    def test_sup(self):
        from smr_phase109_supervisor_identity import build_supervisor_identity
        r=build_supervisor_identity()
        self.assertEqual(r["phase109_supervisor_identity"]["readiness_status"],"partial_ready")
class T109DualControl(unittest.TestCase):
    def test_dual(self):
        from smr_phase109_dual_control_rule import build_dual_control_rule
        r=build_dual_control_rule()
        self.assertTrue(r["phase109_dual_control_rule"]["enforced"])
class T109SameOpForbidden(unittest.TestCase):
    def test_same(self):
        from smr_phase109_same_operator_forbidden import build_same_operator_forbidden
        r=build_same_operator_forbidden()
        self.assertTrue(r["phase109_same_operator_forbidden"]["enforced"])
class T109ManualOverride(unittest.TestCase):
    def test_override(self):
        from smr_phase109_manual_override_identity import build_manual_override_identity
        r=build_manual_override_identity()
        self.assertTrue(r["phase109_manual_override_identity"]["supervisor_must_differ_from_operator"])
class T109KillSwitchOperator(unittest.TestCase):
    def test_ks(self):
        from smr_phase109_kill_switch_operator_identity import build_kill_switch_operator_identity
        r=build_kill_switch_operator_identity()
        self.assertTrue(r["phase109_kill_switch_operator_identity"]["dual_authorization_for_exit"])
class T109PaperExecutionDep(unittest.TestCase):
    def test_dep(self):
        from smr_phase109_paper_execution_identity_dependency import build_paper_execution_identity_dependency
        r=build_paper_execution_identity_dependency()
        self.assertFalse(r["phase109_paper_execution_identity_dependency"]["ready_for_paper_execution"])
class T109AuditLog(unittest.TestCase):
    def test_audit(self):
        from smr_phase109_identity_audit_log import build_identity_audit_log_schema
        r=build_identity_audit_log_schema()
        self.assertEqual(r["phase109_identity_audit_log"]["readiness_status"],"ready")
class T109ProvisioningManifest(unittest.TestCase):
    def test_manifest(self):
        from smr_phase109_identity_provisioning_manifest import build_identity_provisioning_manifest
        r=build_identity_provisioning_manifest()
        self.assertEqual(r["phase109_identity_provisioning_manifest"]["manifest"]["provisioning_status"],"not_started")
class T109Checklist(unittest.TestCase):
    def test_cl(self):
        from smr_phase109_identity_readiness_checklist import build_identity_readiness_checklist
        r=build_identity_readiness_checklist()
        self.assertFalse(r["phase109_identity_readiness_checklist"]["ready_for_paper_execution"])
        self.assertEqual(r["phase109_identity_readiness_checklist"]["blockers_remaining"],3)
class T109Simulation(unittest.TestCase):
    def test_sim(self):
        from smr_phase109_no_order_identity_simulation import run_no_order_identity_simulation
        r=run_no_order_identity_simulation()
        self.assertEqual(r["phase109_no_order_identity_simulation"]["violations"],0)
        self.assertEqual(r["phase109_no_order_identity_simulation"]["account_created"],0)
class T109ViolationClassifier(unittest.TestCase):
    def test_vc(self):
        from smr_phase109_identity_violation_classifier import build_identity_violation_classifier
        r=build_identity_violation_classifier()
        self.assertTrue(r["phase109_identity_violation_classifier"]["no_order_created"])
class T109Scorecard(unittest.TestCase):
    def test_sc(self):
        from smr_phase109_identity_readiness_scorecard import build_identity_readiness_scorecard
        r=build_identity_readiness_scorecard()
        self.assertEqual(r["phase109_identity_readiness_scorecard"]["operator_identity_missing"],"partially_addressed")
class T109Report(unittest.TestCase):
    def test_rpt(self):
        from smr_phase109_identity_readiness_report import build_identity_readiness_report
        r=build_identity_readiness_report()
        self.assertEqual(r["phase109_identity_readiness_report"]["identity_readiness"],"partial_ready")
class T109Guard(unittest.TestCase):
    def test_guard(self):
        from smr_phase109_identity_cannot_conclude_guard import run_identity_guard
        r=run_identity_guard()
        self.assertEqual(r["phase109_guard"]["overall"],"pass")
        self.assertEqual(r["phase109_guard"]["violations"],0)
        self.assertTrue(r["phase109_guard"]["paper_execution_still_blocked"])
class T109Backlog(unittest.TestCase):
    def test_bl(self):
        from smr_phase109_backlog_update import build_backlog_update
        r=build_backlog_update()
        self.assertEqual(r["phase109_backlog_update"]["phase109_status"]["operator_identity_missing"],"partially_addressed")
class T109Dashboard(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase109_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase109");self.assertTrue(d["identity_readiness_only"])
            self.assertEqual(d["account_created"],0)
        finally:sys.argv=old
class T109Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase109_operator_identity_readiness import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase109_pipeline"]
            self.assertTrue(d["identity_readiness_only"]);self.assertFalse(d["paper_execution_enabled"])
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase109_operator_identity_readiness import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase109_pipeline"]
            self.assertFalse(d["ready_for_paper_execution"]);self.assertFalse(d["mock_used"])
            self.assertEqual(d["account_created"],0);self.assertEqual(d["sso_connected"],0)
        finally:sys.argv=old
    def test_skip(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase109_operator_identity_readiness import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase109_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertEqual(d["violations"],0)
        finally:sys.argv=old
if __name__=="__main__":unittest.main()
