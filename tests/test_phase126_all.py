import unittest,sys,os,json,io,contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
class T126Cfg(unittest.TestCase):
    def test_load(self):from smr_phase126_config import load_config;c=load_config();self.assertEqual(c["phase"],"phase126");self.assertTrue(c["signal_effectiveness_review_enabled"])
class T126Domain(unittest.TestCase):
    def test_domains(self):from smr_phase126_domain import build_domain;r=build_domain();self.assertTrue(r["phase126_domain"]["total"]>=12)
class T126Schema(unittest.TestCase):
    def test_schema(self):from smr_phase126_schema import build_schema;r=build_schema();self.assertTrue(r["phase126_schema"]["no_trade_fields"])
class T126Taxonomy(unittest.TestCase):
    def test_tax(self):from smr_phase126_taxonomy import build_taxonomy;r=build_taxonomy();self.assertEqual(r["phase126_taxonomy"]["total"],8)
class T126SignalLoader(unittest.TestCase):
    def test_sl(self):from smr_phase126_signal_loader import build_signal_loader;r=build_signal_loader();self.assertTrue(r["phase126_signal_loader"]["insufficient_sample_ready"])
class T126OutcomeLoader(unittest.TestCase):
    def test_ol(self):from smr_phase126_outcome_loader import build_outcome_loader;r=build_outcome_loader();self.assertEqual(r["phase126_outcome_loader"]["signals_loaded"],0)
class T126ContextLoader(unittest.TestCase):
    def test_cl(self):from smr_phase126_context_loader import build_context_loader;r=build_context_loader();self.assertTrue(r["phase126_context_loader"]["contexts"]>=2)
class T126Metrics(unittest.TestCase):
    def test_m(self):from smr_phase126_metric_registry import build_metric_registry;r=build_metric_registry();self.assertTrue(r["phase126_metric_registry"]["no_financial_metrics"])
class T126OutcomeLinker(unittest.TestCase):
    def test_lk(self):from smr_phase126_outcome_linker import build_outcome_linker;r=build_outcome_linker();self.assertTrue(r["phase126_outcome_linker"]["no_trade_linking"])
class T126Usefulness(unittest.TestCase):
    def test_u(self):from smr_phase126_usefulness import build_usefulness;r=build_usefulness();self.assertTrue(r["phase126_usefulness"]["not_buy_sell_rating"]);self.assertEqual(len(r["phase126_usefulness"]["ratings"]),5)
class T126Noise(unittest.TestCase):
    def test_n(self):from smr_phase126_noise import build_noise;r=build_noise();self.assertTrue(r["phase126_noise"]["not_signal_quality_baseline"]);self.assertEqual(len(r["phase126_noise"]["levels"]),5)
class T126SourceReview(unittest.TestCase):
    def test_sr(self):from smr_phase126_source_review import build_source_review;r=build_source_review();self.assertTrue(r["phase126_source_review"]["no_source_elimination"])
class T126BriefReview(unittest.TestCase):
    def test_br(self):from smr_phase126_brief_review import build_brief_review;r=build_brief_review();self.assertTrue(r["phase126_brief_review"]["no_trade_section_assessment"])
class T126WatchlistReview(unittest.TestCase):
    def test_wr(self):from smr_phase126_watchlist_review import build_watchlist_review;r=build_watchlist_review();self.assertTrue(r["phase126_watchlist_review"]["no_trade_signal"]);self.assertEqual(r["phase126_watchlist_review"]["tickers_reviewed"],8)
class T126Scoring(unittest.TestCase):
    def test_sc(self):from smr_phase126_scoring import build_scoring;r=build_scoring();self.assertEqual(r["phase126_scoring"]["trade_actions"],0);self.assertTrue(r["phase126_scoring"]["no_trade_adjustment"])
class T126Board(unittest.TestCase):
    def test_board(self):from smr_phase126_board import build_board;r=build_board();self.assertTrue(r["phase126_board"]["not_trade_board"])
class T126BriefMd(unittest.TestCase):
    def test_brief(self):from smr_phase126_brief import build_brief_md;r=build_brief_md();self.assertIn("300394",r);self.assertIn("111-126",r)
class T126MemoryWriter(unittest.TestCase):
    def test_mw(self):from smr_phase126_memory_writer import build_memory_writer;r=build_memory_writer();self.assertTrue(r["phase126_memory_writer"]["gitignored"])
class T126Guard(unittest.TestCase):
    def test_grd(self):from smr_phase126_guard import run_guard;r=run_guard();self.assertEqual(r["phase126_guard"]["overall"],"pass");self.assertEqual(r["phase126_guard"]["violations"],0)
class T126Backlog(unittest.TestCase):
    def test_blg(self):from smr_phase126_backlog import build_backlog;r=build_backlog();self.assertIn("phase127",r["phase126_backlog"]["next_phase"]);self.assertEqual(r["phase126_backlog"]["phase111_126_mainline"],"complete")
class T126Dash(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase126_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase126");self.assertEqual(d["phase111_126_mainline"],"complete")
        finally:sys.argv=old
class T126Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase126_signal_effectiveness_review import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase126_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertEqual(d["trade_actions"],0)
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase126_signal_effectiveness_review import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase126_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertEqual(d["phase111_126_mainline"],"complete")
        finally:sys.argv=old
    def test_skip(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase126_signal_effectiveness_review import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase126_pipeline"]
            self.assertEqual(d["guard"],"pass")
        finally:sys.argv=old
