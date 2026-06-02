import unittest,sys,os,json,io,contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
class T122Cfg(unittest.TestCase):
    def test_load(self):from smr_phase122_config import load_config;self.assertEqual(load_config()["phase"],"phase122")
class T122Domain(unittest.TestCase):
    def test_domains(self):from smr_phase122_domain_registry import build_domain_registry;r=build_domain_registry();self.assertTrue(r["phase122_domain_registry"]["total"]>=10)
class T122LoadP117(unittest.TestCase):
    def test_p117(self):from smr_phase122_load_phase117 import load_phase117_outputs;r=load_phase117_outputs();self.assertTrue(r["phase122_phase117_loader"]["modules_loaded"]>=4)
class T122LoadP121(unittest.TestCase):
    def test_p121(self):from smr_phase122_load_phase121 import load_phase121_outputs;r=load_phase121_outputs();self.assertTrue(r["phase122_phase121_loader"]["source_candidates"]>=10)
class T122LoadP116(unittest.TestCase):
    def test_p116(self):from smr_phase122_load_phase116 import load_phase116_outputs;r=load_phase116_outputs();self.assertTrue(r["phase122_phase116_loader"]["tickers_loaded"]>=6)
class T122LoadP115(unittest.TestCase):
    def test_p115(self):from smr_phase122_load_phase115 import load_phase115_outputs;r=load_phase115_outputs();self.assertTrue(r["phase122_phase115_loader"]["candidate_categories"]>=4)
class T122LoadP114(unittest.TestCase):
    def test_p114(self):from smr_phase122_load_phase114 import load_phase114_outputs;r=load_phase114_outputs();self.assertTrue(r["phase122_phase114_loader"]["catalyst_types"]>=8)
class T122Aggregator(unittest.TestCase):
    def test_agg(self):from smr_phase122_brief_aggregator import build_brief_aggregator;r=build_brief_aggregator();self.assertEqual(r["phase122_brief_aggregator"]["inputs_loaded"],5)
class T122Observed(unittest.TestCase):
    def test_obs(self):from smr_phase122_observed_first import build_observed_first;r=build_observed_first();self.assertTrue(r["phase122_observed_first"]["no_trade_advice"])
class T122Digest(unittest.TestCase):
    def test_dig(self):from smr_phase122_evidence_digest import build_evidence_digest;r=build_evidence_digest();self.assertTrue(r["phase122_evidence_digest"]["total_sources"]>=4)
class T122Cards(unittest.TestCase):
    def test_cards(self):from smr_phase122_ticker_cards import build_ticker_cards;r=build_ticker_cards();self.assertEqual(r["phase122_ticker_cards"]["total"],7)
class T122Opportunity(unittest.TestCase):
    def test_opp(self):from smr_phase122_opportunity_section import build_opportunity_section;r=build_opportunity_section();self.assertIn("NVDA",str(r["phase122_opportunity"]["active_catalysts"]))
class T122RiskGap(unittest.TestCase):
    def test_risk(self):from smr_phase122_risk_gap_section import build_risk_gap_section;r=build_risk_gap_section();self.assertEqual(r["phase122_risk_gap"]["pending_sources"],12)
class T122Owner(unittest.TestCase):
    def test_owner(self):from smr_phase122_owner_actions import build_owner_actions;r=build_owner_actions();self.assertTrue(r["phase122_owner_actions"]["owner_action_count"]>=3)
class T122StyleRules(unittest.TestCase):
    def test_rules(self):from smr_phase122_style_rules import load_style_rules;r=load_style_rules();self.assertTrue(len(r["phase122_style_rules"]["forbidden_terms"])>10)
class T122Markdown(unittest.TestCase):
    def test_md(self):from smr_phase122_markdown_brief import build_markdown_brief;r=build_markdown_brief();self.assertIn("300394",r["phase122_markdown_brief"]["markdown"]);self.assertIn("NVDA",r["phase122_markdown_brief"]["markdown"])
class T122JsonSummary(unittest.TestCase):
    def test_json(self):from smr_phase122_json_summary import build_json_summary;r=build_json_summary();self.assertEqual(r["phase122_json_summary"]["tickers_covered"],7)
class T122Lint(unittest.TestCase):
    def test_lint(self):from smr_phase122_brief_lint import run_brief_lint;r=run_brief_lint();self.assertEqual(r["phase122_brief_lint"]["overall"],"pass");self.assertEqual(r["phase122_brief_lint"]["violations"],0)
class T122Archive(unittest.TestCase):
    def test_arch(self):from smr_phase122_archive_writer import build_archive_writer;r=build_archive_writer();self.assertTrue(r["phase122_archive_writer"]["gitignored"])
class T122Guard(unittest.TestCase):
    def test_guard(self):from smr_phase122_cannot_conclude_guard import run_cannot_conclude_guard;r=run_cannot_conclude_guard();self.assertEqual(r["phase122_guard"]["overall"],"pass");self.assertEqual(r["phase122_guard"]["violations"],0)
class T122Backlog(unittest.TestCase):
    def test_blg(self):from smr_phase122_backlog_update import build_backlog_update;r=build_backlog_update();self.assertIn("phase123",r["phase122_backlog"]["next_phase"])
class T122Dash(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase122_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase122");self.assertTrue(d["daily_research_brief_enabled"])
        finally:sys.argv=old
class T122Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase122_daily_research_brief_v2 import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase122_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertTrue(d["brief_generated"])
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase122_daily_research_brief_v2 import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase122_pipeline"]
            self.assertEqual(d["brief_lint"],"pass");self.assertEqual(d["trade_recommendation_created"],0)
        finally:sys.argv=old
    def test_skip(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase122_daily_research_brief_v2 import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase122_pipeline"]
            self.assertEqual(d["guard"],"pass")
        finally:sys.argv=old
