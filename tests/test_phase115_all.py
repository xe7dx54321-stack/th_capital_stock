import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
class T115Cfg(unittest.TestCase):
    def test_load(self):from smr_phase115_config import load_config;self.assertEqual(load_config()["phase"],"phase115")
    def test_research(self):from smr_phase115_config import is_research_only;self.assertTrue(is_research_only())
class T115Domain(unittest.TestCase):
    def test_domains(self):from smr_phase115_domain_registry import build_domain_registry;r=build_domain_registry();self.assertTrue(r["phase115_domain_registry"]["total_domains"]>=7)
class T115Loader(unittest.TestCase):
    def test_load(self):from smr_phase115_candidate_loader import load_all_candidates;r=load_all_candidates();self.assertTrue(r["phase115_candidate_loader"]["total"]>=5);self.assertEqual(r["phase115_candidate_loader"]["blocked"],1)
class T115Classifier(unittest.TestCase):
    def test_cls(self):from smr_phase115_status_classifier import build_status_classifier;r=build_status_classifier();self.assertTrue(r["phase115_status_classifier"]["all_not_trade"])
class T115Board(unittest.TestCase):
    def test_board(self):from smr_phase115_category_board import build_category_board;r=build_category_board();b=r["phase115_category_board"];self.assertTrue(b["not_trade_board"]);self.assertTrue(b["300394_visible"])
class T115Evidence(unittest.TestCase):
    def test_ev(self):from smr_phase115_evidence_summary import build_evidence_summary;r=build_evidence_summary();self.assertTrue(r["phase115_evidence_summary"]["all_not_trade"])
class T115Risk(unittest.TestCase):
    def test_risk(self):from smr_phase115_risk_summary import build_risk_summary;r=build_risk_summary();self.assertTrue(r["phase115_risk_summary"]["all_not_trade"]);self.assertTrue(r["phase115_risk_summary"]["300394_visible"])
class T115Actions(unittest.TestCase):
    def test_ap(self):from smr_phase115_action_planner import build_action_planner;r=build_action_planner();a=r["phase115_action_planner"];self.assertTrue(a["total"]>=4);self.assertEqual(a["trade_actions"],0)
class T115Blocked(unittest.TestCase):
    def test_bp(self):from smr_phase115_blocked_panel import build_blocked_panel;r=build_blocked_panel();self.assertTrue(r["phase115_blocked_panel"]["300394_visible"])
class T115RiskPanel(unittest.TestCase):
    def test_rp(self):from smr_phase115_risk_catalyst_panel import build_risk_catalyst_panel;r=build_risk_catalyst_panel();self.assertTrue(r["phase115_risk_catalyst_panel"]["all_not_trade"])
class T115NewOpp(unittest.TestCase):
    def test_nb(self):from smr_phase115_new_opportunity_board import build_new_opportunity_board;r=build_new_opportunity_board();self.assertTrue(r["phase115_new_opportunity_board"]["all_not_trade"])
class T115Brief(unittest.TestCase):
    def test_brief(self):from smr_phase115_brief import build_candidate_board_brief_md;r=build_candidate_board_brief_md();self.assertIn("NVDA",r);self.assertIn("300394",r)
class T115Guard(unittest.TestCase):
    def test_guard(self):from smr_phase115_cannot_conclude_guard import run_candidate_board_guard;r=run_candidate_board_guard();self.assertEqual(r["phase115_guard"]["overall"],"pass");self.assertEqual(r["phase115_guard"]["violations"],0)
class T115Backlog(unittest.TestCase):
    def test_bl(self):from smr_phase115_backlog_update import build_backlog_update;r=build_backlog_update();self.assertIn("phase116",r["phase115_backlog"]["next_phase_recommendation"])
class T115Dash(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase115_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase115")
        finally:sys.argv=old
class T115Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase115_candidate_board import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase115_pipeline"]
            self.assertTrue(d["research_only"]);self.assertEqual(d["paper_order_created"],0)
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase115_candidate_board import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase115_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertEqual(d["violations"],0)
        finally:sys.argv=old
    def test_skip(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase115_candidate_board import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase115_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertTrue(d["candidates"]>=4)
        finally:sys.argv=old
if __name__=="__main__":unittest.main()
