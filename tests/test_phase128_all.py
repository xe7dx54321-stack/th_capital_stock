import unittest,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

from smr_phase128_config import load_config
from smr_phase128_domain_registry import build_domain_registry
from smr_phase128_pending_source_loader import load_pending_sources
from smr_phase128_known_gap_loader import load_known_gaps
from smr_phase128_probe_policy import build_probe_policy
from smr_phase128_probe_target_planner import plan_probe_targets
from smr_phase128_source_request_adapter import build_request_adapter,probe_url
from smr_phase128_official_source_probe import probe_official_sources
from smr_phase128_third_party_source_probe import probe_third_party_sources
from smr_phase128_quote_source_probe import probe_quote_sources
from smr_phase128_news_event_probe import probe_news_event_sources
from smr_phase128_transcript_guidance_probe import probe_transcript_guidance_sources
from smr_phase128_probe_result_normalizer import normalize_probe_results
from smr_phase128_availability_classifier import classify_availability
from smr_phase128_failure_reason_classifier import classify_failure_reasons
from smr_phase128_content_usability_checker import check_content_usability
from smr_phase128_source_coverage_update import build_source_coverage_update
from smr_phase128_pending_network_closeout import build_pending_network_closeout
from smr_phase128_source_validation_gap_register import build_source_validation_gap_register
from smr_phase128_integration_update import build_integration_update
from smr_phase128_validation_board import build_validation_board
from smr_phase128_validation_brief import build_validation_brief_md
from smr_phase128_validation_memory import build_validation_memory
from smr_phase128_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase128_backlog_update import build_backlog_update

class TestPhase128Config(unittest.TestCase):
    def test_loads(self):
        c=load_config()
        self.assertEqual(c["phase"],"phase128")
    def test_strategy(self):
        c=load_config()
        self.assertEqual(c["strategy"],"external_network_source_probe_and_validation")
    def test_research_only(self):
        c=load_config()
        self.assertTrue(c["research_only"])
    def test_safety(self):
        c=load_config()
        s=c["safety"]
        self.assertFalse(s["mock"])
        self.assertFalse(s["fixture"])
        self.assertEqual(s["paper_order"],0)
        self.assertFalse(s["trade_recommendation_allowed"])
        self.assertFalse(s["target_price_output_allowed"])
        self.assertFalse(s["position_sizing_allowed"])

class TestPhase128DomainRegistry(unittest.TestCase):
    def test_has_domains(self):
        d=build_domain_registry()
        self.assertGreater(d["phase128_domain_registry"]["total"],10)

class TestPhase128PendingSourceLoader(unittest.TestCase):
    def test_has_sources(self):
        s=load_pending_sources()
        self.assertEqual(s["phase128_pending_source_loader"]["total"],12)

class TestPhase128KnownGapLoader(unittest.TestCase):
    def test_300394_retained(self):
        g=load_known_gaps()
        self.assertTrue(g["phase128_known_gap_loader"]["300394_retained"])
        self.assertTrue(g["phase128_known_gap_loader"]["688041_retained"])

class TestPhase128ProbePolicy(unittest.TestCase):
    def test_save_raw_false(self):
        p=build_probe_policy()
        self.assertFalse(p["phase128_probe_policy"]["rules"]["save_raw_content"])
    def test_classification_levels(self):
        p=build_probe_policy()
        self.assertIn("available",p["phase128_probe_policy"]["classification_levels"])

class TestPhase128ProbeTargetPlanner(unittest.TestCase):
    def test_has_targets(self):
        t=plan_probe_targets()
        self.assertEqual(t["phase128_probe_target_planner"]["total"],12)

class TestPhase128SourceRequestAdapter(unittest.TestCase):
    def test_builds(self):
        a=build_request_adapter()
        self.assertFalse(a["phase128_source_request_adapter"]["save_raw"])
    def test_probe_url_bad(self):
        r=probe_url("https://nonexistent.invalid.test",timeout=3)
        self.assertIn(r["status"],["blocked","unknown"])
        self.assertFalse(r["reachable"])

class TestPhase128OfficialSourceProbe(unittest.TestCase):
    def test_skip_network(self):
        r=probe_official_sources(skip_network=True)
        self.assertGreater(r["phase128_official_source_probe"]["total"],0)
        self.assertEqual(r["phase128_official_source_probe"]["available"],0)
    def test_execute(self):
        r=probe_official_sources(skip_network=False)
        self.assertIn("total",r["phase128_official_source_probe"])
        self.assertFalse(r["phase128_official_source_probe"]["raw_saved"])

class TestPhase128ThirdPartySourceProbe(unittest.TestCase):
    def test_skip_network(self):
        r=probe_third_party_sources(skip_network=True)
        self.assertEqual(r["phase128_third_party_source_probe"]["total"],5)
    def test_akshare_available(self):
        r=probe_third_party_sources(skip_network=False)
        results=r["phase128_third_party_source_probe"]["results"]
        akshare=[x for x in results if x["source_id"]=="akshare_hk"]
        if akshare: self.assertEqual(akshare[0]["probe_status"],"available")

class TestPhase128QuoteSourceProbe(unittest.TestCase):
    def test_probes(self):
        r=probe_quote_sources(skip_network=False)
        self.assertEqual(r["phase128_quote_source_probe"]["total"],1)
    def test_skip_network(self):
        r=probe_quote_sources(skip_network=True)
        self.assertEqual(r["phase128_quote_source_probe"]["skipped"],1)

class TestPhase128NewsEventProbe(unittest.TestCase):
    def test_skip_network(self):
        r=probe_news_event_sources(skip_network=True)
        self.assertEqual(r["phase128_news_event_probe"]["total"],2)

class TestPhase128TranscriptGuidanceProbe(unittest.TestCase):
    def test_manual_required(self):
        r=probe_transcript_guidance_sources(skip_network=False)
        self.assertEqual(r["phase128_transcript_guidance_probe"]["manual_required"],1)

class TestPhase128ProbeResultNormalizer(unittest.TestCase):
    def test_normalizes(self):
        r=normalize_probe_results(skip_network=True)
        self.assertGreater(r["phase128_probe_result_normalizer"]["total"],0)
        self.assertFalse(r["phase128_probe_result_normalizer"]["raw_saved"])

class TestPhase128AvailabilityClassifier(unittest.TestCase):
    def test_classifies(self):
        r=classify_availability(skip_network=True)
        self.assertIn("counts",r["phase128_availability_classifier"])
    def test_execute(self):
        r=classify_availability(skip_network=False)
        self.assertIn("counts",r["phase128_availability_classifier"])

class TestPhase128FailureReasonClassifier(unittest.TestCase):
    def test_classifies(self):
        r=classify_failure_reasons(skip_network=True)
        self.assertIn("total_failures",r["phase128_failure_reason_classifier"])

class TestPhase128ContentUsabilityChecker(unittest.TestCase):
    def test_checks(self):
        r=check_content_usability(skip_network=True)
        self.assertIn("total",r["phase128_content_usability_checker"])

class TestPhase128SourceCoverageUpdate(unittest.TestCase):
    def test_updates(self):
        r=build_source_coverage_update(skip_network=True)
        self.assertEqual(r["phase128_source_coverage_update"]["tickers_updated"],4)

class TestPhase128PendingNetworkCloseout(unittest.TestCase):
    def test_closeout(self):
        r=build_pending_network_closeout(skip_network=True)
        self.assertEqual(r["phase128_pending_network_closeout"]["pending_network_before"],12)
    def test_after_lte_before(self):
        r=build_pending_network_closeout(skip_network=False)
        self.assertLessEqual(r["phase128_pending_network_closeout"]["pending_network_after"],r["phase128_pending_network_closeout"]["pending_network_before"])

class TestPhase128SourceValidationGapRegister(unittest.TestCase):
    def test_300394_retained(self):
        r=build_source_validation_gap_register(skip_network=False)
        self.assertTrue(r["phase128_source_validation_gap_register"]["300394_retained"])
        self.assertTrue(r["phase128_source_validation_gap_register"]["688041_retained"])

class TestPhase128IntegrationUpdate(unittest.TestCase):
    def test_integration(self):
        r=build_integration_update(skip_network=False)
        self.assertIn("phase121",r["phase128_integration_update"]["phases_updated"])

class TestPhase128ValidationBoard(unittest.TestCase):
    def test_not_trade(self):
        r=build_validation_board(skip_network=False)
        self.assertTrue(r["phase128_validation_board"]["not_trade_board"])

class TestPhase128ValidationBrief(unittest.TestCase):
    def test_has_content(self):
        md=build_validation_brief_md(skip_network=False)
        self.assertIn("External Source",md)

class TestPhase128ValidationMemory(unittest.TestCase):
    def test_gitignored(self):
        r=build_validation_memory()
        self.assertTrue(r["phase128_validation_memory"]["gitignored"])

class TestPhase128CannotConcludeGuard(unittest.TestCase):
    def test_pass(self):
        r=run_cannot_conclude_guard(skip_network=False)
        self.assertEqual(r["phase128_cannot_conclude_guard"]["overall"],"pass")
        self.assertEqual(r["phase128_cannot_conclude_guard"]["violations"],0)

class TestPhase128BacklogUpdate(unittest.TestCase):
    def test_next_phase(self):
        r=build_backlog_update(skip_network=False)
        self.assertIn("phase129",r["phase128_backlog_update"]["next_phase"])
    def test_deprecated(self):
        r=build_backlog_update(skip_network=False)
        for d in ["paper_order","target_price","position_sizing","profit_loss"]:
            self.assertIn(d,r["phase128_backlog_update"]["deprecated_forever"])

class TestPhase128RegressionGate(unittest.TestCase):
    def test_phase127_regression(self):
        from smr_phase127_guard import run_guard
        g=run_guard()
        self.assertEqual(g["phase127_guard"]["overall"],"pass")
    def test_300394_visible(self):
        r=build_source_validation_gap_register(skip_network=False)
        gaps=r["phase128_source_validation_gap_register"]["gaps"]
        found=[g for g in gaps if "300394" in g.get("source_id","")]
        self.assertGreater(len(found),0)
    def test_688041_visible(self):
        r=build_source_validation_gap_register(skip_network=False)
        gaps=r["phase128_source_validation_gap_register"]["gaps"]
        found=[g for g in gaps if "688041" in g.get("source_id","")]
        self.assertGreater(len(found),0)

if __name__=="__main__":
    unittest.main()
