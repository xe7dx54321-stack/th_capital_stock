import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
class T119Cfg(unittest.TestCase):
    def test_load(self):from smr_phase119_config import load_config;self.assertEqual(load_config()["phase"],"phase119")
class T119Domain(unittest.TestCase):
    def test_domains(self):from smr_phase119_domain_registry import build_domain_registry;r=build_domain_registry();self.assertTrue(r["phase119_domain_registry"]["total"]>=9)
class T119HealthLoader(unittest.TestCase):
    def test_hl(self):from smr_phase119_health_loader import load_phase118_health;r=load_phase118_health();self.assertTrue(r["phase119_health_loader"]["above_threshold"])
class T119Runstate(unittest.TestCase):
    def test_rs(self):from smr_phase119_runstate_loader import load_phase117_runstate;r=load_phase117_runstate();self.assertTrue(r["phase119_runstate_loader"]["all_modules_pass"])
class T119Watchlist(unittest.TestCase):
    def test_wl(self):from smr_phase119_watchlist_loader import load_phase116_watchlist;r=load_phase116_watchlist();self.assertEqual(r["phase119_watchlist_loader"]["states"]["catalyst_active"],2)
class T119Gaps(unittest.TestCase):
    def test_gaps(self):from smr_phase119_gap_inventory import build_gap_inventory;r=build_gap_inventory();g=r["phase119_gap_inventory"];self.assertTrue(g["total"]>=5);self.assertTrue(g["critical"]>=1);self.assertTrue(g["all_not_trade"])
class T119Priority(unittest.TestCase):
    def test_gp(self):from smr_phase119_gap_priority import classify_gap_priorities;r=classify_gap_priorities();self.assertTrue(r["phase119_gap_priority"]["all_not_trade"])
class T119AutoFix(unittest.TestCase):
    def test_af(self):from smr_phase119_auto_fix_assessor import assess_auto_fix;r=assess_auto_fix();self.assertTrue(r["phase119_auto_fix_assessor"]["auto_fix_count"]>=1)
class T119SourceRefresh(unittest.TestCase):
    def test_sr(self):from smr_phase119_source_refresh_planner import plan_source_refresh;r=plan_source_refresh();self.assertTrue(r["phase119_source_refresh_planner"]["all_not_trade"])
class T119EvidenceGap(unittest.TestCase):
    def test_eg(self):from smr_phase119_evidence_gap_planner import plan_evidence_gap_close;r=plan_evidence_gap_close();self.assertTrue(r["phase119_evidence_gap_planner"]["all_not_trade"])
class T119Blocker(unittest.TestCase):
    def test_bp(self):from smr_phase119_blocker_planner import plan_blocker_resolution;r=plan_blocker_resolution();self.assertTrue(r["phase119_blocker_planner"]["all_not_trade"])
class T119Reliability(unittest.TestCase):
    def test_rp(self):from smr_phase119_reliability_planner import plan_reliability_improvement;r=plan_reliability_improvement();self.assertTrue(r["phase119_reliability_planner"]["all_not_trade"])
class T119Feedback(unittest.TestCase):
    def test_fi(self):from smr_phase119_feedback_intake import build_feedback_intake_schema;r=build_feedback_intake_schema();self.assertTrue(r["phase119_feedback_intake"]["all_not_trade"])
class T119Actions(unittest.TestCase):
    def test_aq(self):from smr_phase119_action_queue import build_improvement_queue;r=build_improvement_queue();a=r["phase119_improvement_queue"];self.assertTrue(a["total"]>=4);self.assertEqual(a["trade_actions"],0)
class T119Verification(unittest.TestCase):
    def test_vc(self):from smr_phase119_verification_checklist import build_verification_checklist;r=build_verification_checklist();self.assertTrue(r["phase119_verification_checklist"]["all_pass"])
class T119Board(unittest.TestCase):
    def test_board(self):from smr_phase119_improvement_board import build_improvement_board;r=build_improvement_board();b=r["phase119_improvement_board"];self.assertTrue(b["not_trade_board"]);self.assertTrue(b["300394_visible"])
class T119Memory(unittest.TestCase):
    def test_mw(self):from smr_phase119_memory_writer import build_memory_writer;r=build_memory_writer();self.assertTrue(r["phase119_memory_writer"]["gitignored"])
class T119Brief(unittest.TestCase):
    def test_brief(self):from smr_phase119_brief import build_improvement_brief_md;r=build_improvement_brief_md();self.assertIn("97",r);self.assertIn("300394",r)
class T119Guard(unittest.TestCase):
    def test_guard(self):from smr_phase119_cannot_conclude_guard import run_improvement_guard;r=run_improvement_guard();self.assertEqual(r["phase119_guard"]["overall"],"pass");self.assertEqual(r["phase119_guard"]["violations"],0)
class T119Backlog(unittest.TestCase):
    def test_bl(self):from smr_phase119_backlog_update import build_backlog_update;r=build_backlog_update();self.assertIn("phase120",r["phase119_backlog"]["next_phase_recommendation"])
class T119Dash(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase119_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase119")
        finally:sys.argv=old
class T119Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase119_continuous_improvement import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase119_pipeline"]
            self.assertTrue(d["total_gaps"]>=4);self.assertEqual(d["paper_order_created"],0)
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase119_continuous_improvement import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase119_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertTrue(d["verification_pass"])
        finally:sys.argv=old
    def test_skip(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase119_continuous_improvement import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase119_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertTrue(d["auto_fixable"]>=1)
        finally:sys.argv=old
if __name__=="__main__":unittest.main()
