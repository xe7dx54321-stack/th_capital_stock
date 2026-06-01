import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
class T111Cfg(unittest.TestCase):
    def test_load(self):from smr_phase111_config import load_config;self.assertEqual(load_config()["phase"],"phase111")
    def test_personal(self):from smr_phase111_config import is_personal_use_system;self.assertTrue(is_personal_use_system())
    def test_owner(self):from smr_phase111_config import is_owner_mode_enabled;self.assertTrue(is_owner_mode_enabled())
    def test_multi_disabled(self):from smr_phase111_config import is_multi_user_disabled;self.assertTrue(is_multi_user_disabled())
    def test_paper_disabled(self):from smr_phase111_config import is_paper_execution_disabled;self.assertTrue(is_paper_execution_disabled())
class T111Domain(unittest.TestCase):
    def test_domains(self):from smr_phase111_owner_mode_domain_registry import build_owner_mode_domain_registry;r=build_owner_mode_domain_registry();d=r["phase111_owner_mode_domain_registry"];self.assertTrue(d["active_domains"]>=4);self.assertTrue(d["personal_use_system"]);self.assertFalse(d["multi_user_system"])
class T111Identity(unittest.TestCase):
    def test_identity(self):from smr_phase111_owner_identity import build_owner_identity;r=build_owner_identity();i=r["phase111_owner_identity"];self.assertTrue(i["owner_identity_set"]);self.assertTrue(i["owner_is_sole_user"]);self.assertEqual(i["identity_conflicts"],0)
class T111ConfirmationGate(unittest.TestCase):
    def test_gate(self):from smr_phase111_owner_confirmation_gate import build_owner_confirmation_gate;r=build_owner_confirmation_gate();g=r["phase111_owner_confirmation_gate"];self.assertTrue(g["all_pass"]);self.assertTrue(g["no_order_no_trade"])
class T111Taxonomy(unittest.TestCase):
    def test_tax(self):from smr_phase111_research_action_taxonomy import build_research_action_taxonomy;r=build_research_action_taxonomy();t=r["phase111_research_action_taxonomy"];self.assertTrue(t["no_order_actions"]);self.assertTrue(t["research_only_mode"]);self.assertTrue(t["active_actions"]>=8)
class T111ActionQueue(unittest.TestCase):
    def test_queue(self):from smr_phase111_owner_action_queue import build_owner_action_queue;r=build_owner_action_queue();q=r["phase111_owner_action_queue"];self.assertTrue(q["no_trade_actions"]);self.assertEqual(q["paper_order_count"],0);self.assertEqual(q["live_trade_count"],0)
class T111RiskGate(unittest.TestCase):
    def test_risk(self):from smr_phase111_research_risk_gate import build_research_risk_gate;r=build_research_risk_gate();g=r["phase111_research_risk_gate"];self.assertTrue(g["all_pass"]);self.assertTrue(g["critical_pass"]);self.assertTrue(g["trading_disabled"])
class T111Safety(unittest.TestCase):
    def test_safety(self):from smr_phase111_research_safety_mode import build_research_safety_mode;r=build_research_safety_mode();s=r["phase111_research_safety_mode"];self.assertTrue(s["trading_permanently_disabled"]);self.assertTrue(s["all_safety_checks_pass"])
class T111Evidence(unittest.TestCase):
    def test_evidence(self):from smr_phase111_evidence_first_policy import build_evidence_first_policy;r=build_evidence_first_policy();e=r["phase111_evidence_first_policy"];self.assertTrue(e["all_enforced"]);self.assertTrue(e["evidence_required_before_decision"])
class T111MultiUserDep(unittest.TestCase):
    def test_mu_dep(self):from smr_phase111_multi_user_deprecation_map import build_multi_user_deprecation_map;r=build_multi_user_deprecation_map();m=r["phase111_multi_user_deprecation_map"];self.assertTrue(m["all_deprecated"]);self.assertTrue(m["multi_user_assignment_no_longer_required"])
class T111PaperExecDep(unittest.TestCase):
    def test_pe_dep(self):from smr_phase111_paper_execution_deprecation_map import build_paper_execution_deprecation_map;r=build_paper_execution_deprecation_map();p=r["phase111_paper_execution_deprecation_map"];self.assertTrue(p["all_permanently_disabled"]);self.assertTrue(p["paper_execution_fully_deprecated"])
class T111Audit(unittest.TestCase):
    def test_audit(self):from smr_phase111_personal_audit_log import build_personal_audit_log;r=build_personal_audit_log();a=r["phase111_personal_audit_log"];self.assertEqual(a["paper_order_events"],0);self.assertEqual(a["trade_events"],0);self.assertTrue(a["audit_trail_complete"])
class T111DashState(unittest.TestCase):
    def test_ds(self):from smr_phase111_personal_dashboard_state import build_personal_dashboard_state;r=build_personal_dashboard_state();d=r["phase111_personal_dashboard_state"];self.assertTrue(d["research_only_view"]);self.assertTrue(d["no_trading_panels"]);self.assertIn("300394.SZ",d["blocked_tickers"])
class T111Migration(unittest.TestCase):
    def test_mig(self):from smr_phase111_owner_mode_migration_report import build_owner_mode_migration_report;r=build_owner_mode_migration_report();m=r["phase111_owner_mode_migration_report"];self.assertEqual(m["pivot_direction"],"personal_owner_research_support");self.assertEqual(m["next_phase"],"phase112_opportunity_radar_v1")
class T111Guard(unittest.TestCase):
    def test_guard(self):from smr_phase111_cannot_conclude_guard import run_owner_mode_cannot_conclude_guard;r=run_owner_mode_cannot_conclude_guard();self.assertEqual(r["phase111_guard"]["overall"],"pass");self.assertEqual(r["phase111_guard"]["violations"],0)
class T111Backlog(unittest.TestCase):
    def test_bl(self):from smr_phase111_backlog_reframe import build_backlog_reframe;r=build_backlog_reframe();b=r["phase111_backlog_reframe"];self.assertTrue(b["phase111_status"]["paper_execution_permanently_disabled"]);self.assertEqual(b["next_recommended_action"],"start_phase112_opportunity_radar_v1")
class T111Dash(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase111_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase111");self.assertTrue(d["personal_use_system"]);self.assertFalse(d["multi_user_assignment_required"])
        finally:sys.argv=old
class T111Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase111_personal_owner_mode import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase111_pipeline"]
            self.assertTrue(d["personal_use_system"]);self.assertFalse(d["multi_user_assignment_required"]);self.assertEqual(d["paper_order_created"],0)
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase111_personal_owner_mode import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase111_pipeline"]
            self.assertFalse(d["paper_execution_enabled"]);self.assertFalse(d["live_trading_enabled"]);self.assertEqual(d["guard"],"pass")
        finally:sys.argv=old
    def test_skip(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase111_personal_owner_mode import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase111_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertEqual(d["violations"],0)
        finally:sys.argv=old
if __name__=="__main__":unittest.main()
