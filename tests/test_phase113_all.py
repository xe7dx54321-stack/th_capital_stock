import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
class T113Cfg(unittest.TestCase):
    def test_load(self):from smr_phase113_config import load_config;self.assertEqual(load_config()["phase"],"phase113")
    def test_research_only(self):from smr_phase113_config import is_research_only;self.assertTrue(is_research_only())
    def test_scoring(self):from smr_phase113_config import is_cross_source_scoring_enabled;self.assertTrue(is_cross_source_scoring_enabled())
class T113Domain(unittest.TestCase):
    def test_domains(self):from smr_phase113_scoring_domain_registry import build_scoring_domain_registry;r=build_scoring_domain_registry();d=r["phase113_scoring_domain_registry"];self.assertTrue(d["total_domains"]>=7);self.assertTrue(d["all_research_only"])
class T113Loader(unittest.TestCase):
    def test_load(self):from smr_phase113_candidate_loader import load_phase112_candidates;r=load_phase112_candidates();l=r["phase113_candidate_loader"];self.assertTrue(l["candidates_loaded"]>=5);self.assertEqual(l["blocked"],1)
class T113SourceWeight(unittest.TestCase):
    def test_weight(self):from smr_phase113_source_reliability_weight import build_source_reliability_weight;r=build_source_reliability_weight();s=r["phase113_source_reliability_weight"];self.assertTrue(s["total_weighted"]>=4)
class T113EvidenceQuality(unittest.TestCase):
    def test_ev(self):from smr_phase113_evidence_quality_scorer import build_evidence_quality_scorer;r=build_evidence_quality_scorer();e=r["phase113_evidence_quality_scorer"];self.assertTrue(e["total_scored"]>=4)
class T113CrossSource(unittest.TestCase):
    def test_cs(self):from smr_phase113_cross_source_confirmation_scorer import build_cross_source_scorer;r=build_cross_source_scorer();c=r["phase113_cross_source_scorer"];self.assertTrue(c["multi_source_confirmed"]>=1)
class T113Novelty(unittest.TestCase):
    def test_nf(self):from smr_phase113_novelty_freshness_scorer import build_novelty_freshness_scorer;r=build_novelty_freshness_scorer();n=r["phase113_novelty_freshness_scorer"];self.assertTrue(n["total_scored"]>=4)
class T113HardData(unittest.TestCase):
    def test_hd(self):from smr_phase113_hard_data_support_scorer import build_hard_data_support_scorer;r=build_hard_data_support_scorer();h=r["phase113_hard_data_support_scorer"];self.assertTrue(h["total_scored"]>=4)
class T113Risk(unittest.TestCase):
    def test_rd(self):from smr_phase113_risk_discount_model import build_risk_discount_model;r=build_risk_discount_model();d=r["phase113_risk_discount_model"];self.assertTrue(d["high_risk_discount_visible"]);self.assertTrue(d["688041_visible"])
class T113Contradiction(unittest.TestCase):
    def test_cp(self):from smr_phase113_contradiction_penalty_model import build_contradiction_penalty_model;r=build_contradiction_penalty_model();p=r["phase113_contradiction_penalty_model"];self.assertTrue(p["total_penalized"]>=4)
class T113Composite(unittest.TestCase):
    def test_comp(self):from smr_phase113_composite_priority_scorer import build_composite_priority_scorer;r=build_composite_priority_scorer();c=r["phase113_composite_priority_scorer"];self.assertTrue(c["scored_candidates"]>=5);self.assertTrue(c["high"]>=1);self.assertTrue(c["blocked"]>=1);self.assertTrue(c["all_not_trade"])
class T113Explanation(unittest.TestCase):
    def test_expl(self):from smr_phase113_score_explanation_builder import build_score_explanation;r=build_score_explanation();e=r["phase113_score_explanation"];self.assertTrue(e["total_explanations"]>=4);self.assertTrue(e["all_not_trade"])
class T113ActionQueue(unittest.TestCase):
    def test_q(self):from smr_phase113_scored_owner_action_queue import build_scored_owner_action_queue;r=build_scored_owner_action_queue();q=r["phase113_scored_owner_action_queue"];self.assertTrue(q["owner_action_count"]>=4);self.assertEqual(q["trade_actions"],0);self.assertTrue(q["all_not_trade"])
class T113Board(unittest.TestCase):
    def test_board(self):from smr_phase113_scored_opportunity_board import build_scored_opportunity_board;r=build_scored_opportunity_board();b=r["phase113_scored_opportunity_board"];self.assertTrue(b["not_trade_board"]);self.assertTrue(b["300394_blocked_visible"])
class T113Brief(unittest.TestCase):
    def test_brief(self):from smr_phase113_scored_opportunity_brief import build_scored_opportunity_brief_md;r=build_scored_opportunity_brief_md();self.assertIn("NVDA",r);self.assertIn("300394",r)
class T113Guard(unittest.TestCase):
    def test_guard(self):from smr_phase113_cannot_conclude_guard import run_cross_source_scoring_guard;r=run_cross_source_scoring_guard();self.assertEqual(r["phase113_guard"]["overall"],"pass");self.assertEqual(r["phase113_guard"]["violations"],0)
class T113Backlog(unittest.TestCase):
    def test_bl(self):from smr_phase113_backlog_update import build_backlog_update;r=build_backlog_update();b=r["phase113_backlog"];self.assertIn("phase114",b["next_phase_recommendation"]);self.assertTrue(b["cross_source_scoring_capable"])
class T113Dash(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase113_dashboard import main as dm
        old=sys.argv[:]
        try:sys.argv=["d.py","--json"];buf=io.StringIO();contextlib.redirect_stdout(buf);dm()
        finally:sys.argv=old
class T113Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase113_cross_source_scoring import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase113_pipeline"]
            self.assertTrue(d["research_only"]);self.assertEqual(d["paper_order_created"],0)
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase113_cross_source_scoring import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase113_pipeline"]
            self.assertFalse(d["trade_recommendation_allowed"]);self.assertEqual(d["guard"],"pass");self.assertEqual(d["violations"],0)
        finally:sys.argv=old
    def test_skip(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase113_cross_source_scoring import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase113_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertTrue(d["scored_candidates"]>=4)
        finally:sys.argv=old
if __name__=="__main__":unittest.main()
