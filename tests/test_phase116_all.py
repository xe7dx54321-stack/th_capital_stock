import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
class T116Cfg(unittest.TestCase):
    def test_load(self):from smr_phase116_config import load_config;self.assertEqual(load_config()["phase"],"phase116")
    def test_research(self):from smr_phase116_config import is_research_only;self.assertTrue(is_research_only())
class T116Domain(unittest.TestCase):
    def test_domains(self):from smr_phase116_domain_registry import build_domain_registry;r=build_domain_registry();self.assertTrue(r["phase116_domain_registry"]["total"]>=7)
class T116Universe(unittest.TestCase):
    def test_uni(self):from smr_phase116_universe_loader import load_watchlist_universe;r=load_watchlist_universe();u=r["phase116_universe"];self.assertEqual(u["total"],8);self.assertEqual(u["states"]["blocked"],1)
class T116BoardLoader(unittest.TestCase):
    def test_bl(self):from smr_phase115_board_loader import load_phase115_candidate_board;r=load_phase115_candidate_board();self.assertEqual(r["phase116_board_loader"]["total_candidates"],6)
class T116Schema(unittest.TestCase):
    def test_schema(self):from smr_phase116_state_schema import build_research_state_schema;r=build_research_state_schema();self.assertTrue(r["phase116_state_schema"]["not_trade_schema"])
class T116Classifier(unittest.TestCase):
    def test_cls(self):from smr_phase116_state_classifier import classify_watchlist_states;r=classify_watchlist_states();self.assertTrue(r["phase116_state_classifier"]["all_not_trade"])
class T116Mapper(unittest.TestCase):
    def test_mp(self):from smr_phase116_candidate_mapper import map_candidates_to_watchlist;r=map_candidates_to_watchlist();self.assertTrue(r["phase116_candidate_mapper"]["all_not_trade"])
class T116Evidence(unittest.TestCase):
    def test_ev(self):from smr_phase116_evidence_refresh import build_evidence_refresh;r=build_evidence_refresh();self.assertTrue(r["phase116_evidence_refresh"]["all_not_trade"])
class T116Thesis(unittest.TestCase):
    def test_th(self):from smr_phase116_thesis_summary import build_thesis_summary;r=build_thesis_summary();self.assertTrue(r["phase116_thesis_summary"]["all_not_trade"])
class T116Risk(unittest.TestCase):
    def test_risk(self):from smr_phase116_risk_summary import build_risk_summary;r=build_risk_summary();self.assertTrue(r["phase116_risk_summary"]["all_not_trade"])
class T116Actions(unittest.TestCase):
    def test_ap(self):from smr_phase116_action_planner import build_action_planner;r=build_action_planner();a=r["phase116_action_planner"];self.assertTrue(a["total"]>=5);self.assertEqual(a["trade_actions"],0)
class T116Transition(unittest.TestCase):
    def test_st(self):from smr_phase116_status_transition import build_status_transition;r=build_status_transition();self.assertTrue(r["phase116_status_transition"]["all_not_trade"])
class T116Board(unittest.TestCase):
    def test_board(self):from smr_phase116_research_board import build_research_board;r=build_research_board();b=r["phase116_research_board"];self.assertTrue(b["not_trade_board"]);self.assertTrue(b["300394_visible"])
class T116Memory(unittest.TestCase):
    def test_mem(self):from smr_phase116_memory_writer import build_memory_writer;r=build_memory_writer();self.assertTrue(r["phase116_memory_writer"]["path_ignored"])
class T116Brief(unittest.TestCase):
    def test_brief(self):from smr_phase116_brief import build_watchlist_brief_md;r=build_watchlist_brief_md();self.assertIn("NVDA",r);self.assertIn("300394",r)
class T116Guard(unittest.TestCase):
    def test_guard(self):from smr_phase116_cannot_conclude_guard import run_watchlist_guard;r=run_watchlist_guard();self.assertEqual(r["phase116_guard"]["overall"],"pass");self.assertEqual(r["phase116_guard"]["violations"],0)
class T116Backlog(unittest.TestCase):
    def test_bl(self):from smr_phase116_backlog_update import build_backlog_update;r=build_backlog_update();self.assertIn("phase117",r["phase116_backlog"]["next_phase_recommendation"])
class T116Dash(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase116_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase116")
        finally:sys.argv=old
class T116Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase116_watchlist_research_loop import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase116_pipeline"]
            self.assertTrue(d["research_only"]);self.assertEqual(d["paper_order_created"],0)
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase116_watchlist_research_loop import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase116_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertEqual(d["violations"],0)
        finally:sys.argv=old
    def test_skip(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase116_watchlist_research_loop import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase116_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertTrue(d["tickers"]>=6)
        finally:sys.argv=old
if __name__=="__main__":unittest.main()
