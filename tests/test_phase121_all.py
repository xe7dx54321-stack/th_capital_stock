import unittest,sys,os,json,io,contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
class T121Cfg(unittest.TestCase):
    def test_load(self):from smr_phase121_config import load_config;self.assertEqual(load_config()["phase"],"phase121")
class T121Domain(unittest.TestCase):
    def test_domains(self):from smr_phase121_domain_registry import build_domain_registry;r=build_domain_registry();self.assertTrue(r["phase121_domain_registry"]["total"]>=10)
class T121Universe(unittest.TestCase):
    def test_uni(self):from smr_phase121_target_universe import build_target_universe;r=build_target_universe();self.assertEqual(r["phase121_target_universe"]["tickers_total"],8)
class T121SourceCandidates(unittest.TestCase):
    def test_scr(self):from smr_phase121_source_candidate_registry import build_source_candidate_registry;r=build_source_candidate_registry();self.assertTrue(r["phase121_source_candidate_registry"]["total"]>=10)
class T121OfficialFilings(unittest.TestCase):
    def test_ofr(self):from smr_phase121_official_filing_registry import build_official_filing_registry;r=build_official_filing_registry();self.assertTrue(r["phase121_official_filing_registry"]["total"]>=5)
class T121MarketQuote(unittest.TestCase):
    def test_mqr(self):from smr_phase121_market_quote_registry import build_market_quote_registry;r=build_market_quote_registry();self.assertTrue(r["phase121_market_quote_registry"]["total"]>=2)
class T121NewsEvent(unittest.TestCase):
    def test_ner(self):from smr_phase121_news_event_registry import build_news_event_registry;r=build_news_event_registry();self.assertTrue(r["phase121_news_event_registry"]["total"]>=4)
class T121Transcript(unittest.TestCase):
    def test_tgr(self):from smr_phase121_transcript_guidance_registry import build_transcript_guidance_registry;r=build_transcript_guidance_registry();self.assertTrue(r["phase121_transcript_guidance_registry"]["total"]>=3)
class T121AccessPolicy(unittest.TestCase):
    def test_ap(self):from smr_phase121_source_access_policy import build_source_access_policy;r=build_source_access_policy();self.assertTrue(r["phase121_source_access_policy"]["enforced"])
class T121Connector(unittest.TestCase):
    def test_cs(self):from smr_phase121_connector_skeleton import build_connector_skeleton;r=build_connector_skeleton();self.assertTrue(r["phase121_connector_skeleton"]["total"]>=4)
class T121HKAdapter(unittest.TestCase):
    def test_hk(self):from smr_phase121_hk_external_adapter import build_hk_external_adapter;r=build_hk_external_adapter();self.assertEqual(r["phase121_hk_external_adapter"]["total"],2)
class T121USAdapter(unittest.TestCase):
    def test_us(self):from smr_phase121_us_external_adapter import build_us_external_adapter;r=build_us_external_adapter();self.assertEqual(r["phase121_us_external_adapter"]["total"],2)
class T121Probe(unittest.TestCase):
    def test_dry(self):from smr_phase121_source_probe import probe_sources;r=probe_sources("dry-run");self.assertEqual(r["phase121_source_probe"]["mode"],"dry-run")
    def test_exec(self):from smr_phase121_source_probe import probe_sources;r=probe_sources("execute");self.assertEqual(r["phase121_source_probe"]["mode"],"execute")
    def test_skip(self):from smr_phase121_source_probe import probe_sources;r=probe_sources("skip-network");self.assertEqual(r["phase121_source_probe"]["mode"],"skip-network")
class T121CoverageMatrix(unittest.TestCase):
    def test_mat(self):from smr_phase121_source_coverage_matrix import build_source_coverage_matrix;r=build_source_coverage_matrix();self.assertTrue(r["phase121_source_coverage_matrix"]["single_source_risk_reduced_count"]>=2)
class T121EvidenceNorm(unittest.TestCase):
    def test_evn(self):from smr_phase121_external_evidence_normalization import build_external_evidence_normalization;r=build_external_evidence_normalization();self.assertIn("news_headline",r["phase121_external_evidence_normalization"]["rules"])
class T121Reliability(unittest.TestCase):
    def test_rel(self):from smr_phase121_cross_source_reliability import build_cross_source_reliability;r=build_cross_source_reliability();self.assertIn("NVDA",r["phase121_cross_source_reliability"]["before"])
class T121GapRegister(unittest.TestCase):
    def test_grp(self):from smr_phase121_source_gap_register import build_source_gap_register;r=build_source_gap_register();self.assertTrue(r["phase121_source_gap_register"]["total"]>=5)
class T121Integration(unittest.TestCase):
    def test_int(self):from smr_phase121_integration_report import build_integration_report;r=build_integration_report();self.assertTrue(r["phase121_integration_report"]["no_breaking_change"])
class T121Board(unittest.TestCase):
    def test_brd(self):from smr_phase121_expansion_board import build_expansion_board;r=build_expansion_board();self.assertTrue(r["phase121_expansion_board"]["not_trade_board"])
class T121Brief(unittest.TestCase):
    def test_brief(self):from smr_phase121_expansion_brief import build_expansion_brief_md;r=build_expansion_brief_md();self.assertIn("300394",r);self.assertIn("NVDA",r)
class T121Guard(unittest.TestCase):
    def test_grd(self):from smr_phase121_cannot_conclude_guard import run_cannot_conclude_guard;r=run_cannot_conclude_guard();self.assertEqual(r["phase121_guard"]["overall"],"pass");self.assertEqual(r["phase121_guard"]["violations"],0)
class T121Backlog(unittest.TestCase):
    def test_blg(self):from smr_phase121_backlog_update import build_backlog_update;r=build_backlog_update();self.assertIn("phase122",r["phase121_backlog"]["next_phase"])
class T121Dash(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase121_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase121");self.assertEqual(d["hk_tickers"],2)
        finally:sys.argv=old
class T121Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase121_external_source_expansion import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase121_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertEqual(d["paper_order_created"],0)
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase121_external_source_expansion import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase121_pipeline"]
            self.assertEqual(d["guard"],"pass")
        finally:sys.argv=old
    def test_skip(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase121_external_source_expansion import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase121_pipeline"]
            self.assertEqual(d["guard"],"pass")
        finally:sys.argv=old
