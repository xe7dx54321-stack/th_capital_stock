import unittest,sys,os,json,io,contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
class T123Cfg(unittest.TestCase):
    def test_load(self):from smr_phase123_config import load_config;c=load_config();self.assertEqual(c["phase"],"phase123");self.assertTrue(c["research_only"])
class T123Domain(unittest.TestCase):
    def test_domains(self):from smr_phase123_domain_registry import build_domain_registry;r=build_domain_registry();self.assertTrue(r["phase123_domain_registry"]["total"]>=12)
class T123Schema(unittest.TestCase):
    def test_schema(self):from smr_phase123_feedback_schema import build_feedback_schema;r=build_feedback_schema();self.assertIn("feedback_id",r["phase123_feedback_schema"]["fields"])
class T123Intake(unittest.TestCase):
    def test_intake(self):from smr_phase123_feedback_intake import build_feedback_intake;r=build_feedback_intake();self.assertTrue(r["phase123_feedback_intake"]["not_trade_template"])
class T123Validation(unittest.TestCase):
    def test_val(self):from smr_phase123_feedback_validation import build_feedback_validation;r=build_feedback_validation();self.assertTrue(r["phase123_feedback_validation"]["rules_count"]>=5)
class T123Classifier(unittest.TestCase):
    def test_clf(self):from smr_phase123_feedback_classifier import build_feedback_classifier;r=build_feedback_classifier();self.assertEqual(r["phase123_feedback_classifier"]["feedback_types"],12)
class T123Linker(unittest.TestCase):
    def test_link(self):from smr_phase123_feedback_entity_linker import build_feedback_entity_linker;r=build_feedback_entity_linker();self.assertTrue(len(r["phase123_feedback_entity_linker"]["linkable_entities"])>=5)
class T123Writer(unittest.TestCase):
    def test_writer(self):from smr_phase123_feedback_memory_writer import build_feedback_memory_writer;r=build_feedback_memory_writer();self.assertTrue(r["phase123_feedback_memory_writer"]["gitignored"])
class T123Reader(unittest.TestCase):
    def test_reader(self):from smr_phase123_feedback_memory_reader import build_feedback_memory_reader;r=build_feedback_memory_reader();self.assertTrue(r["phase123_feedback_memory_reader"]["empty_memory_ready"])
class T123Impact(unittest.TestCase):
    def test_impact(self):from smr_phase123_feedback_impact_scorer import build_feedback_impact_scorer;r=build_feedback_impact_scorer();self.assertTrue(r["phase123_feedback_impact_scorer"]["not_investment_action"])
class T123Opp(unittest.TestCase):
    def test_opp(self):from smr_phase123_opp_adapter import build_opp_adapter;r=build_opp_adapter();self.assertTrue(r["phase123_opp_adapter"]["no_trade"])
class T123Brief(unittest.TestCase):
    def test_brief(self):from smr_phase123_brief_adapter import build_brief_adapter;r=build_brief_adapter();self.assertTrue(r["phase123_brief_adapter"]["no_trade"])
class T123Source(unittest.TestCase):
    def test_source(self):from smr_phase123_source_adapter import build_source_adapter;r=build_source_adapter();self.assertTrue(r["phase123_source_adapter"]["no_trade"])
class T123Watchlist(unittest.TestCase):
    def test_wl(self):from smr_phase123_watchlist_adapter import build_watchlist_adapter;r=build_watchlist_adapter();self.assertTrue(r["phase123_watchlist_adapter"]["no_trade"])
class T123Action(unittest.TestCase):
    def test_ap(self):from smr_phase123_feedback_action_planner import build_feedback_action_planner;r=build_feedback_action_planner();self.assertEqual(r["phase123_feedback_action_planner"]["trade_actions"],0)
class T123Board(unittest.TestCase):
    def test_board(self):from smr_phase123_feedback_board import build_feedback_board;r=build_feedback_board();self.assertTrue(r["phase123_feedback_board"]["not_trade_board"])
class T123BriefMd(unittest.TestCase):
    def test_brief(self):from smr_phase123_feedback_brief import build_feedback_brief_md;r=build_feedback_brief_md();self.assertIn("300394",r);self.assertIn("Safety",r)
class T123Guard(unittest.TestCase):
    def test_grd(self):from smr_phase123_cannot_conclude_guard import run_cannot_conclude_guard;r=run_cannot_conclude_guard();self.assertEqual(r["phase123_guard"]["overall"],"pass");self.assertEqual(r["phase123_guard"]["violations"],0)
class T123Backlog(unittest.TestCase):
    def test_blg(self):from smr_phase123_backlog_update import build_backlog_update;r=build_backlog_update();self.assertIn("phase124",r["phase123_backlog"]["next_phase"])
class T123Dash(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase123_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase123");self.assertTrue(d["owner_feedback_enabled"])
        finally:sys.argv=old
class T123Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase123_owner_feedback_memory import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase123_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertEqual(d["trade_recommendation_created"],0)
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase123_owner_feedback_memory import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase123_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertTrue(d["memory_path_ignored"])
        finally:sys.argv=old
    def test_skip(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase123_owner_feedback_memory import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase123_pipeline"]
            self.assertEqual(d["guard"],"pass")
        finally:sys.argv=old
