import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
class T110Cfg(unittest.TestCase):
    def test_load(self):from smr_phase110_config import load_config;self.assertEqual(load_config()["phase"],"phase110")
    def test_manual(self):from smr_phase110_config import is_manual_assignment_only;self.assertTrue(is_manual_assignment_only())
class T110Domain(unittest.TestCase):
    def test_domains(self):from smr_phase110_assignment_domain_registry import build_assignment_domain_registry;r=build_assignment_domain_registry();self.assertEqual(r["phase110_assignment_domain_registry"]["total_domains"],12);self.assertTrue(r["phase110_assignment_domain_registry"]["all_assignments_pending"])
class T110Matrix(unittest.TestCase):
    def test_matrix(self):from smr_phase110_role_assignment_matrix import build_role_assignment_matrix;r=build_role_assignment_matrix();self.assertEqual(r["phase110_role_assignment_matrix"]["required_roles"],5);self.assertTrue(r["phase110_role_assignment_matrix"]["manual_assignment_required"])
class T110Manifest(unittest.TestCase):
    def test_manifest(self):from smr_phase110_assignment_manifest import build_assignment_manifest;r=build_assignment_manifest();self.assertEqual(r["phase110_assignment_manifest"]["manifest"]["roles_to_assign"],5)
class T110Template(unittest.TestCase):
    def test_template(self):from smr_phase110_assignment_input_template import build_assignment_input_template;r=build_assignment_input_template();self.assertTrue(r["phase110_assignment_input_template"]["all_slots_unfilled"]);self.assertFalse(r["phase110_assignment_input_template"]["real_personal_info"])
class T110Validation(unittest.TestCase):
    def test_rules(self):from smr_phase110_assignment_validation_rules import build_assignment_validation_rules;r=build_assignment_validation_rules();self.assertEqual(r["phase110_assignment_validation_rules"]["total_rules"],5)
class T110Conflict(unittest.TestCase):
    def test_conflict(self):from smr_phase110_role_conflict_checker import run_role_conflict_checker;r=run_role_conflict_checker();self.assertTrue(r["phase110_role_conflict_checker"]["all_enforced"])
class T110SamePerson(unittest.TestCase):
    def test_same(self):from smr_phase110_same_person_assignment_checker import run_same_person_checker;r=run_same_person_checker();self.assertTrue(r["phase110_same_person_checker"]["enforced"])
class T110Dual(unittest.TestCase):
    def test_dual(self):from smr_phase110_dual_control_assignment_checker import run_dual_control_checker;r=run_dual_control_checker();self.assertTrue(r["phase110_dual_control_checker"]["all_distinct_required"])
class T110Supervisor(unittest.TestCase):
    def test_sup(self):from smr_phase110_supervisor_assignment_checker import run_supervisor_checker;r=run_supervisor_checker();self.assertTrue(r["phase110_supervisor_checker"]["blocks_paper_execution"])
class T110KS(unittest.TestCase):
    def test_ks(self):from smr_phase110_kill_switch_operator_checker import run_kill_switch_operator_checker;r=run_kill_switch_operator_checker();self.assertEqual(r["phase110_kill_switch_operator_checker"]["assigned"],0)
class T110Chain(unittest.TestCase):
    def test_chain(self):from smr_phase110_approval_chain_checker import run_approval_chain_checker;r=run_approval_chain_checker();self.assertTrue(r["phase110_approval_chain_checker"]["all_assignments_pending"])
class T110Audit(unittest.TestCase):
    def test_audit(self):from smr_phase110_assignment_audit_log import build_assignment_audit_log;r=build_assignment_audit_log();self.assertEqual(r["phase110_assignment_audit_log"]["readiness_status"],"ready")
class T110Checklist(unittest.TestCase):
    def test_cl(self):from smr_phase110_manual_assignment_checklist import build_manual_assignment_checklist;r=build_manual_assignment_checklist();self.assertFalse(r["phase110_manual_assignment_checklist"]["ready_for_paper_execution"])
class T110Dep(unittest.TestCase):
    def test_dep(self):from smr_phase110_paper_execution_assignment_dependency import build_paper_execution_dependency;r=build_paper_execution_dependency();self.assertFalse(r["phase110_paper_execution_dependency"]["ready_for_paper_execution"])
class T110Sim(unittest.TestCase):
    def test_sim(self):from smr_phase110_no_order_assignment_simulation import run_no_order_assignment_simulation;r=run_no_order_assignment_simulation();self.assertEqual(r["phase110_no_order_simulation"]["violations"],0)
class T110VC(unittest.TestCase):
    def test_vc(self):from smr_phase110_assignment_violation_classifier import build_assignment_violation_classifier;r=build_assignment_violation_classifier();self.assertTrue(r["phase110_assignment_violation_classifier"]["all_detected"])
class T110SC(unittest.TestCase):
    def test_sc(self):from smr_phase110_assignment_readiness_scorecard import build_assignment_scorecard;r=build_assignment_scorecard();self.assertFalse(r["phase110_assignment_scorecard"]["ready_for_paper_execution"])
class T110Guard(unittest.TestCase):
    def test_guard(self):from smr_phase110_assignment_cannot_conclude_guard import run_assignment_guard;r=run_assignment_guard();self.assertEqual(r["phase110_guard"]["overall"],"pass");self.assertEqual(r["phase110_guard"]["violations"],0)
class T110Backlog(unittest.TestCase):
    def test_bl(self):from smr_phase110_backlog_update import build_backlog_update;r=build_backlog_update();self.assertFalse(r["phase110_backlog_update"]["phase110_status"]["ready_for_paper_execution"])
class T110Dash(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase110_dashboard import main as dm;old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase110");self.assertTrue(d["manual_assignment_only"]);self.assertEqual(d["real_operators_assigned"],0)
        finally:sys.argv=old
class T110Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase110_operator_assignment_manifest import main as rm;old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase110_pipeline"]
            self.assertTrue(d["manual_assignment_only"]);self.assertEqual(d["real_operators_assigned"],0)
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase110_operator_assignment_manifest import main as rm;old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase110_pipeline"]
            self.assertFalse(d["ready_for_paper_execution"]);self.assertEqual(d["account_created"],0)
        finally:sys.argv=old
    def test_skip(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase110_operator_assignment_manifest import main as rm;old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase110_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertEqual(d["violations"],0)
        finally:sys.argv=old
if __name__=="__main__":unittest.main()
