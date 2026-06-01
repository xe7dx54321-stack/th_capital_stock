import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
class T112Cfg(unittest.TestCase):
    def test_load(self):from smr_phase112_config import load_config;self.assertEqual(load_config()["phase"],"phase112")
    def test_research_only(self):from smr_phase112_config import is_research_only;self.assertTrue(is_research_only())
    def test_trade_blocked(self):from smr_phase112_config import is_trade_blocked;self.assertTrue(is_trade_blocked())
    def test_universe(self):from smr_phase112_config import get_universe;self.assertEqual(len(get_universe()),8)
class T112Source(unittest.TestCase):
    def test_sources(self):from smr_phase112_opportunity_source_registry import build_opportunity_source_registry;r=build_opportunity_source_registry();s=r["phase112_opportunity_source_registry"];self.assertTrue(s["active_sources"]>=12);self.assertTrue(s["research_only"])
class T112Universe(unittest.TestCase):
    def test_universe(self):from smr_phase112_opportunity_universe_loader import build_opportunity_universe;r=build_opportunity_universe();u=r["phase112_opportunity_universe"];self.assertEqual(u["tickers_total"],8);self.assertEqual(u["radar_enabled"],7);self.assertEqual(u["blocked"],1)
class T112Taxonomy(unittest.TestCase):
    def test_tax(self):from smr_phase112_signal_taxonomy import build_radar_signal_taxonomy;r=build_radar_signal_taxonomy();t=r["phase112_signal_taxonomy"];self.assertTrue(t["total_signals"]>=12);self.assertTrue(t["all_research_only"])
class T112Ingestion(unittest.TestCase):
    def test_sig(self):from smr_phase112_signal_ingestion_adapter import build_signal_ingestion_report;r=build_signal_ingestion_report();s=r["phase112_signal_ingestion"];self.assertTrue(s["signals_loaded"]>=5);self.assertFalse(s["mock_used"])
class T112Candidate(unittest.TestCase):
    def test_pool(self):from smr_phase112_candidate_builder import build_opportunity_candidate_pool;r=build_opportunity_candidate_pool();p=r["phase112_opportunity_candidate_pool"];self.assertTrue(p["candidate_count"]>=5);self.assertTrue(p["not_trade_recommendation"]);self.assertEqual(p["blocked_count"],1)
class T112Evidence(unittest.TestCase):
    def test_ev(self):from smr_phase112_evidence_linkage import build_evidence_linkage;r=build_evidence_linkage();e=r["phase112_evidence_linkage"];self.assertTrue(e["total_linkages"]>=5);self.assertTrue(e["with_evidence"]>=3)
class T112Novelty(unittest.TestCase):
    def test_nov(self):from smr_phase112_novelty_change_detector import build_novelty_change_report;r=build_novelty_change_report();n=r["phase112_novelty_change"];self.assertTrue(n["new_signals"]>=1);self.assertTrue(n["significant_updates"]>=1);self.assertTrue(n["blocked"]>=1)
class T112Strength(unittest.TestCase):
    def test_stre(self):from smr_phase112_signal_strength_classifier import build_signal_strength_report;r=build_signal_strength_report();s=r["phase112_signal_strength"];self.assertTrue(s["strong"]>=1);self.assertTrue(s["all_not_trade_signal"])
class T112Risk(unittest.TestCase):
    def test_risk(self):from smr_phase112_research_risk_gate import build_research_risk_gate;r=build_research_risk_gate();g=r["phase112_research_risk_gate"];self.assertTrue(g["300394_blocked_visible"]);self.assertTrue(g["688041_valuation_gap_visible"]);self.assertTrue(g["critical_risk"]>=1)
class T112Ranking(unittest.TestCase):
    def test_rank(self):from smr_phase112_opportunity_ranking import build_opportunity_ranking;r=build_opportunity_ranking();rk=r["phase112_opportunity_ranking"];self.assertEqual(rk["ranking_type"],"research_priority");self.assertTrue(rk["not_investment_ranking"]);self.assertTrue(rk["no_buy_sell"])
class T112ActionQueue(unittest.TestCase):
    def test_q(self):from smr_phase112_owner_action_queue import build_owner_action_queue;r=build_owner_action_queue();q=r["phase112_owner_action_queue"];self.assertTrue(q["owner_action_count"]>=4);self.assertEqual(q["trade_actions"],0);self.assertTrue(q["all_not_trade"])
class T112Guard(unittest.TestCase):
    def test_guard(self):from smr_phase112_cannot_conclude_guard import run_opportunity_cannot_conclude_guard;r=run_opportunity_cannot_conclude_guard();self.assertEqual(r["phase112_guard"]["overall"],"pass");self.assertEqual(r["phase112_guard"]["violations"],0)
class T112Backlog(unittest.TestCase):
    def test_bl(self):from smr_phase112_backlog_update import build_backlog_update;r=build_backlog_update();b=r["phase112_backlog"];self.assertIn("phase113",b["next_phase_recommendation"]);self.assertTrue(b["opportunity_radar_capable"])
class T112Dash(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase112_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase112");self.assertTrue(d["research_only"]);self.assertFalse(d["trade_recommendation_allowed"]);self.assertEqual(d["paper_order_created"],0)
        finally:sys.argv=old
class T112RadarBoard(unittest.TestCase):
    def test_board(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase112_opportunity_radar_board import main as bm
        old=sys.argv[:]
        try:
            sys.argv=["b.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):bm()
            d=json.loads(buf.getvalue())["phase112_opportunity_radar_board"]
            self.assertTrue(d["research_only"]);self.assertEqual(d["tickers_total"],8);self.assertEqual(d["blocked"],1)
        finally:sys.argv=old
class T112Brief(unittest.TestCase):
    def test_brief(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase112_daily_opportunity_brief import main as brm
        old=sys.argv[:]
        try:
            sys.argv=["br.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):brm()
            d=json.loads(buf.getvalue())["phase112_daily_opportunity_brief"]
            self.assertTrue(d["research_only"]);self.assertEqual(d["trade_recommendation"],0);self.assertEqual(d["target_price"],0)
        finally:sys.argv=old
class T112Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase112_opportunity_radar import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase112_pipeline"]
            self.assertTrue(d["research_only"]);self.assertFalse(d["trade_recommendation_allowed"]);self.assertEqual(d["paper_order_created"],0);self.assertEqual(d["target_price_created"],0)
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase112_opportunity_radar import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase112_pipeline"]
            self.assertFalse(d["paper_execution_enabled"]);self.assertFalse(d["live_trading_enabled"]);self.assertEqual(d["guard"],"pass");self.assertEqual(d["violations"],0)
        finally:sys.argv=old
    def test_skip(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase112_opportunity_radar import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase112_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertTrue(d["candidate_count"]>=4)
        finally:sys.argv=old
if __name__=="__main__":unittest.main()
