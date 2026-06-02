import unittest,sys,os,json,io,contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
class T124Cfg(unittest.TestCase):
    def test_load(self):from smr_phase124_config import load_config;c=load_config();self.assertEqual(c["phase"],"phase124");self.assertTrue(c["research_only"])
class T124Domain(unittest.TestCase):
    def test_domains(self):from smr_phase124_domain_registry import build_domain_registry;r=build_domain_registry();self.assertTrue(r["phase124_domain_registry"]["total"]>=10)
class T124Schema(unittest.TestCase):
    def test_schema(self):from smr_phase124_schema import build_decision_schema;r=build_decision_schema();self.assertIn("decision_id",r["phase124_schema"]["fields"])
class T124Taxonomy(unittest.TestCase):
    def test_tax(self):from smr_phase124_taxonomy import build_decision_taxonomy;r=build_decision_taxonomy();self.assertEqual(r["phase124_taxonomy"]["total"],10)
class T124Context(unittest.TestCase):
    def test_ctx(self):from smr_phase124_context_loader import build_context_loader;r=build_context_loader();self.assertTrue(r["phase124_context_loader"]["context_types"]>=5)
class T124Intake(unittest.TestCase):
    def test_intake(self):from smr_phase124_intake import build_intake_template;r=build_intake_template();self.assertTrue(r["phase124_intake"]["not_trade_template"])
class T124Validation(unittest.TestCase):
    def test_val(self):from smr_phase124_validation import build_decision_validation;r=build_decision_validation();self.assertTrue(r["phase124_validation"]["trade_rejected"])
class T124EvidenceLinker(unittest.TestCase):
    def test_ev(self):from smr_phase124_evidence_linker import build_evidence_linker;r=build_evidence_linker();self.assertTrue(r["phase124_evidence_linker"]["link_types"]>=3)
class T124FeedbackLinker(unittest.TestCase):
    def test_fb(self):from smr_phase124_feedback_linker import build_feedback_linker;r=build_feedback_linker();self.assertTrue(r["phase124_feedback_linker"]["link_bidirectional"])
class T124WatchlistLinker(unittest.TestCase):
    def test_wl(self):from smr_phase124_watchlist_linker import build_watchlist_linker;r=build_watchlist_linker();self.assertTrue(r["phase124_watchlist_linker"]["not_trade_update"])
class T124Writer(unittest.TestCase):
    def test_w(self):from smr_phase124_writer import build_journal_writer;r=build_journal_writer();self.assertTrue(r["phase124_writer"]["gitignored"])
class T124Reader(unittest.TestCase):
    def test_r(self):from smr_phase124_reader import build_journal_reader;r=build_journal_reader();self.assertTrue(r["phase124_reader"]["empty_journal_ready"])
class T124Rationale(unittest.TestCase):
    def test_rat(self):from smr_phase124_rationale import build_decision_rationale;r=build_decision_rationale();self.assertTrue(r["phase124_rationale"]["not_investment_rationale"])
class T124Followup(unittest.TestCase):
    def test_fup(self):from smr_phase124_followup import build_followup_planner;r=build_followup_planner();self.assertTrue(r["phase124_followup"]["not_trade_followup"])
class T124Review(unittest.TestCase):
    def test_rev(self):from smr_phase124_review_schedule import build_review_schedule;r=build_review_schedule();self.assertTrue(r["phase124_review_schedule"]["not_trade_review"])
class T124Board(unittest.TestCase):
    def test_board(self):from smr_phase124_board import build_decision_board;r=build_decision_board();self.assertTrue(r["phase124_board"]["not_trade_board"])
class T124Brief(unittest.TestCase):
    def test_brief(self):from smr_phase124_brief import build_decision_brief_md;r=build_decision_brief_md();self.assertIn("300394",r);self.assertIn("Safety",r)
class T124Guard(unittest.TestCase):
    def test_grd(self):from smr_phase124_guard import run_cannot_conclude_guard;r=run_cannot_conclude_guard();self.assertEqual(r["phase124_guard"]["overall"],"pass");self.assertEqual(r["phase124_guard"]["violations"],0)
class T124Backlog(unittest.TestCase):
    def test_blg(self):from smr_phase124_backlog import build_backlog_update;r=build_backlog_update();self.assertIn("phase125",r["phase124_backlog"]["next_phase"])
class T124Dash(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase124_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase124");self.assertTrue(d["decision_journal_enabled"])
        finally:sys.argv=old
class T124Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase124_decision_journal import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase124_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertEqual(d["trade_recommendation_created"],0)
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase124_decision_journal import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase124_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertTrue(d["journal_path_ignored"])
        finally:sys.argv=old
    def test_skip(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase124_decision_journal import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase124_pipeline"]
            self.assertEqual(d["guard"],"pass")
        finally:sys.argv=old
