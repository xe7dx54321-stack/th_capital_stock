import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
class T114Cfg(unittest.TestCase):
    def test_load(self):from smr_phase114_config import load_config;self.assertEqual(load_config()["phase"],"phase114")
    def test_research(self):from smr_phase114_config import is_research_only;self.assertTrue(is_research_only())
    def test_catalyst(self):from smr_phase114_config import is_catalyst_enabled;self.assertTrue(is_catalyst_enabled())
class T114Domain(unittest.TestCase):
    def test_domains(self):from smr_phase114_catalyst_domain_registry import build_catalyst_domain_registry;r=build_catalyst_domain_registry();self.assertTrue(r["phase114_catalyst_domain_registry"]["total_domains"]>=7)
class T114Loader(unittest.TestCase):
    def test_load(self):from smr_phase114_candidate_loader import load_phase113_scored_candidates;r=load_phase113_scored_candidates();self.assertTrue(r["phase114_candidate_loader"]["candidates_loaded"]>=5)
class T114CatalystTax(unittest.TestCase):
    def test_tax(self):from smr_phase114_catalyst_taxonomy import build_catalyst_taxonomy;r=build_catalyst_taxonomy();self.assertTrue(r["phase114_catalyst_taxonomy"]["total_types"]>=9);self.assertTrue(r["phase114_catalyst_taxonomy"]["all_not_trade"])
class T114InflectionTax(unittest.TestCase):
    def test_inf(self):from smr_phase114_inflection_signal_taxonomy import build_inflection_signal_taxonomy;r=build_inflection_signal_taxonomy();self.assertTrue(r["phase114_inflection_signal_taxonomy"]["all_not_trade"])
class T114EvidenceMapper(unittest.TestCase):
    def test_ev(self):from smr_phase114_catalyst_evidence_mapper import build_catalyst_evidence_mapper;r=build_catalyst_evidence_mapper();self.assertTrue(r["phase114_catalyst_evidence_mapper"]["catalysts_found"]>=4)
class T114Expectation(unittest.TestCase):
    def test_exp(self):from smr_phase114_expectation_change_detector import build_expectation_change_detector;r=build_expectation_change_detector();self.assertTrue(r["phase114_expectation_change_detector"]["all_not_trade"])
class T114Thesis(unittest.TestCase):
    def test_th(self):from smr_phase114_thesis_change_detector import build_thesis_change_detector;r=build_thesis_change_detector();self.assertTrue(r["phase114_thesis_change_detector"]["all_not_trade"])
class T114Timing(unittest.TestCase):
    def test_tm(self):from smr_phase114_catalyst_timing_classifier import build_catalyst_timing_classifier;r=build_catalyst_timing_classifier();self.assertTrue(r["phase114_catalyst_timing_classifier"]["immediate"]>=1)
class T114Confidence(unittest.TestCase):
    def test_cf(self):from smr_phase114_catalyst_confidence_scorer import build_catalyst_confidence_scorer;r=build_catalyst_confidence_scorer();self.assertTrue(r["phase114_catalyst_confidence_scorer"]["high_confidence"]>=1);self.assertTrue(r["phase114_catalyst_confidence_scorer"]["all_not_trade"])
class T114Risk(unittest.TestCase):
    def test_rk(self):from smr_phase114_catalyst_risk_gate import build_catalyst_risk_gate;r=build_catalyst_risk_gate();g=r["phase114_catalyst_risk_gate"];self.assertTrue(g["300394_blocked_visible"]);self.assertTrue(g["all_not_trade"])
class T114Explanation(unittest.TestCase):
    def test_expl(self):from smr_phase114_inflection_explanation_builder import build_inflection_explanation;r=build_inflection_explanation();self.assertTrue(r["phase114_inflection_explanation"]["all_not_trade"])
class T114ActionQueue(unittest.TestCase):
    def test_q(self):from smr_phase114_catalyst_action_queue import build_catalyst_action_queue;r=build_catalyst_action_queue();q=r["phase114_catalyst_action_queue"];self.assertTrue(q["total"]>=4);self.assertEqual(q["trade_actions"],0);self.assertTrue(q["all_not_trade"])
class T114Board(unittest.TestCase):
    def test_board(self):from smr_phase114_catalyst_radar_board import build_catalyst_radar_board;r=build_catalyst_radar_board();self.assertTrue(r["phase114_catalyst_radar_board"]["not_trade_board"]);self.assertTrue(r["phase114_catalyst_radar_board"]["300394_visible"])
class T114Brief(unittest.TestCase):
    def test_brief(self):from smr_phase114_catalyst_brief import build_catalyst_brief_md;r=build_catalyst_brief_md();self.assertIn("NVDA",r);self.assertIn("300394",r)
class T114Guard(unittest.TestCase):
    def test_guard(self):from smr_phase114_cannot_conclude_guard import run_catalyst_guard;r=run_catalyst_guard();self.assertEqual(r["phase114_guard"]["overall"],"pass");self.assertEqual(r["phase114_guard"]["violations"],0)
class T114Backlog(unittest.TestCase):
    def test_bl(self):from smr_phase114_backlog_update import build_backlog_update;r=build_backlog_update();self.assertIn("phase115",r["phase114_backlog"]["next_phase_recommendation"])
class T114Dash(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase114_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase114")
        finally:sys.argv=old
class T114Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase114_catalyst_inflection_detector import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase114_pipeline"]
            self.assertTrue(d["research_only"]);self.assertEqual(d["paper_order_created"],0)
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase114_catalyst_inflection_detector import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase114_pipeline"]
            self.assertFalse(d["trade_recommendation_allowed"]);self.assertEqual(d["guard"],"pass")
        finally:sys.argv=old
    def test_skip(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase114_catalyst_inflection_detector import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase114_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertTrue(d["catalysts_found"]>=3)
        finally:sys.argv=old
if __name__=="__main__":unittest.main()
