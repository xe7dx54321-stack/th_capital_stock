import unittest,sys,os,json,io,contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
class T125Cfg(unittest.TestCase):
    def test_load(self):from smr_phase125_config import load_config;c=load_config();self.assertEqual(c["phase"],"phase125");self.assertTrue(c["research_only"]);self.assertFalse(c["profit_loss_tracking_allowed"])
class T125Domain(unittest.TestCase):
    def test_domains(self):from smr_phase125_domain import build_domain_registry;r=build_domain_registry();self.assertTrue(r["phase125_domain"]["total"]>=12)
class T125Schema(unittest.TestCase):
    def test_schema(self):from smr_phase125_schema import build_schema;r=build_schema();self.assertTrue(r["phase125_schema"]["no_profit_loss_fields"])
class T125Taxonomy(unittest.TestCase):
    def test_tax(self):from smr_phase125_taxonomy import build_taxonomy;r=build_taxonomy();self.assertEqual(r["phase125_taxonomy"]["total"],12);self.assertTrue(r["phase125_taxonomy"]["no_profit_loss"])
class T125DecisionLoader(unittest.TestCase):
    def test_dl(self):from smr_phase125_decision_loader import build_decision_loader;r=build_decision_loader();self.assertTrue(r["phase125_decision_loader"]["empty_journal_ready"])
class T125Context(unittest.TestCase):
    def test_ctx(self):from smr_phase125_context_loader import build_context_loader;r=build_context_loader();self.assertTrue(r["phase125_context_loader"]["contexts"]>=5)
class T125Intake(unittest.TestCase):
    def test_intake(self):from smr_phase125_intake import build_intake;r=build_intake();self.assertTrue(r["phase125_intake"]["not_profit_loss_template"])
class T125Validation(unittest.TestCase):
    def test_val(self):from smr_phase125_validation import build_validation;r=build_validation();self.assertTrue(r["phase125_validation"]["finance_tracking_rejected"])
class T125DecisionLinker(unittest.TestCase):
    def test_dl(self):from smr_phase125_decision_linker import build_decision_linker;r=build_decision_linker();self.assertTrue(r["phase125_decision_linker"]["link_bidirectional"])
class T125EvidenceLinker(unittest.TestCase):
    def test_el(self):from smr_phase125_evidence_linker import build_evidence_linker;r=build_evidence_linker();self.assertTrue(r["phase125_evidence_linker"]["link_types"]>=2)
class T125WatchlistLinker(unittest.TestCase):
    def test_wl(self):from smr_phase125_watchlist_linker import build_watchlist_linker;r=build_watchlist_linker();self.assertTrue(r["phase125_watchlist_linker"]["not_trade_update"])
class T125Classifier(unittest.TestCase):
    def test_clf(self):from smr_phase125_classifier import build_classifier;r=build_classifier();self.assertTrue(r["phase125_classifier"]["no_financial_status"])
class T125Writer(unittest.TestCase):
    def test_w(self):from smr_phase125_writer import build_writer;r=build_writer();self.assertTrue(r["phase125_writer"]["gitignored"])
class T125Reader(unittest.TestCase):
    def test_r(self):from smr_phase125_reader import build_reader;r=build_reader();self.assertTrue(r["phase125_reader"]["empty_outcome_ready"])
class T125Board(unittest.TestCase):
    def test_board(self):from smr_phase125_board import build_board;r=build_board();self.assertTrue(r["phase125_board"]["not_trade_board"])
class T125Brief(unittest.TestCase):
    def test_brief(self):from smr_phase125_brief import build_brief_md;r=build_brief_md();self.assertIn("300394",r);self.assertIn("profit",r.lower())
class T125Learning(unittest.TestCase):
    def test_ls(self):from smr_phase125_learning_signal import build_learning_signal;r=build_learning_signal();self.assertTrue(r["phase125_learning_signal"]["no_financial_signals"])
class T125Followup(unittest.TestCase):
    def test_fup(self):from smr_phase125_followup import build_followup;r=build_followup();self.assertTrue(r["phase125_followup"]["not_trade_followup"])
class T125Guard(unittest.TestCase):
    def test_grd(self):from smr_phase125_guard import run_guard;r=run_guard();self.assertEqual(r["phase125_guard"]["overall"],"pass");self.assertEqual(r["phase125_guard"]["violations"],0)
class T125Backlog(unittest.TestCase):
    def test_blg(self):from smr_phase125_backlog import build_backlog;r=build_backlog();self.assertIn("phase126",r["phase125_backlog"]["next_phase"])
class T125Dash(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase125_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase125");self.assertFalse(d["profit_loss_tracking_created"])
        finally:sys.argv=old
class T125Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase125_outcome_tracking import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase125_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertFalse(d["profit_loss_tracking_created"])
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase125_outcome_tracking import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase125_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertEqual(d["trade_recommendation_created"],0)
        finally:sys.argv=old
    def test_skip(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase125_outcome_tracking import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase125_pipeline"]
            self.assertEqual(d["guard"],"pass")
        finally:sys.argv=old
