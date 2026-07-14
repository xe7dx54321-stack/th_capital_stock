import unittest,json,sys,os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "08_scripts" / "lib"))

from smr_phase129_config import load_config
from smr_phase129_domain_registry import build_domain_registry
from smr_phase129_blocked_source_loader import load_blocked_sources
from smr_phase129_official_source_identity_map import build_official_source_identity_map
from smr_phase129_sec_edgar_fallback import build_sec_edgar_fallback
from smr_phase129_hkex_fallback import build_hkex_fallback
from smr_phase129_transcript_fallback import build_transcript_fallback
from smr_phase129_mirror_registry import build_mirror_registry
from smr_phase129_third_party_equivalent_registry import build_third_party_equivalent_registry
from smr_phase129_access_route_planner import build_access_route_planner
from smr_phase129_fallback_probe_policy import build_fallback_probe_policy
from smr_phase129_fallback_probe_executor import execute_fallback_probe
from smr_phase129_api_key_classifier import classify_api_key_required
from smr_phase129_proxy_classifier import classify_proxy_required
from smr_phase129_manual_workflow_builder import build_manual_workflow
from smr_phase129_equivalence_scorer import build_equivalence_scorer
from smr_phase129_coverage_update_builder import build_coverage_update
from smr_phase129_gap_register import build_gap_register
from smr_phase129_integration_update import build_integration_update
from smr_phase129_fallback_board import build_fallback_board
from smr_phase129_fallback_brief import build_fallback_brief_md
from smr_phase129_fallback_memory import build_fallback_memory
from smr_phase129_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase129_backlog_update import build_backlog_update

class TestPhase129Config(unittest.TestCase):
    def test_loads(self): c=load_config();self.assertEqual(c["phase"],"phase129")
    def test_research_only(self): self.assertTrue(load_config()["research_only"])
    def test_safety(self):
        s=load_config()["safety"]
        self.assertFalse(s["mock"]);self.assertFalse(s["fixture"])
        self.assertEqual(s["paper_order"],0)

class TestPhase129DomainRegistry(unittest.TestCase):
    def test_has_domains(self): self.assertGreater(build_domain_registry()["phase129_domain_registry"]["total"],10)

class TestPhase129BlockedSourceLoader(unittest.TestCase):
    def test_loads(self):
        r=load_blocked_sources()
        self.assertIn("total",r["phase129_blocked_source_loader"])

class TestPhase129OfficialSourceIdentityMap(unittest.TestCase):
    def test_has_all(self):
        r=build_official_source_identity_map()
        self.assertIn("sec_edgar",r["phase129_official_source_identity_map"]["sources"])

class TestPhase129SecEdgarFallback(unittest.TestCase):
    def test_all_have_fallback(self):
        r=build_sec_edgar_fallback()
        self.assertTrue(r["phase129_sec_edgar_fallback"]["all_have_fallback"])

class TestPhase129HkexFallback(unittest.TestCase):
    def test_all_have_fallback(self):
        r=build_hkex_fallback()
        self.assertTrue(r["phase129_hkex_fallback"]["all_have_fallback"])

class TestPhase129TranscriptFallback(unittest.TestCase):
    def test_manual_retained(self):
        r=build_transcript_fallback()
        self.assertTrue(r["phase129_transcript_fallback"]["transcript_full_manual_required"])

class TestPhase129MirrorRegistry(unittest.TestCase):
    def test_all_available(self):
        r=build_mirror_registry()
        self.assertTrue(r["phase129_mirror_registry"]["all_mirrors_available"])

class TestPhase129ThirdPartyEquivalentRegistry(unittest.TestCase):
    def test_has_equivalents(self):
        r=build_third_party_equivalent_registry()
        self.assertGreater(r["phase129_third_party_equivalent_registry"]["available"],0)

class TestPhase129AccessRoutePlanner(unittest.TestCase):
    def test_all_have_route(self):
        r=build_access_route_planner()
        self.assertTrue(r["phase129_access_route_planner"]["all_have_route"])

class TestPhase129FallbackProbePolicy(unittest.TestCase):
    def test_no_raw(self):
        r=build_fallback_probe_policy()
        self.assertFalse(r["phase129_fallback_probe_policy"]["rules"]["save_raw_content"])

class TestPhase129FallbackProbeExecutor(unittest.TestCase):
    def test_execute(self):
        r=execute_fallback_probe(skip_network=False)
        self.assertGreater(r["phase129_fallback_probe_executor"]["available"],0)
    def test_skip_network(self):
        r=execute_fallback_probe(skip_network=True)
        self.assertEqual(r["phase129_fallback_probe_executor"]["skipped"],r["phase129_fallback_probe_executor"]["total"])

class TestPhase129ApiKeyClassifier(unittest.TestCase):
    def test_classifies(self):
        r=classify_api_key_required()
        self.assertIn("total",r["phase129_api_key_classifier"])

class TestPhase129ProxyClassifier(unittest.TestCase):
    def test_classifies(self):
        r=classify_proxy_required()
        self.assertIn("total",r["phase129_proxy_classifier"])

class TestPhase129ManualWorkflowBuilder(unittest.TestCase):
    def test_builds(self):
        r=build_manual_workflow()
        self.assertTrue(r["phase129_manual_workflow_builder"]["all_require_owner_action"])

class TestPhase129EquivalenceScorer(unittest.TestCase):
    def test_has_high(self):
        r=build_equivalence_scorer()
        self.assertGreater(r["phase129_equivalence_scorer"]["high_equivalence"],0)

class TestPhase129CoverageUpdateBuilder(unittest.TestCase):
    def test_maintained(self):
        r=build_coverage_update()
        self.assertTrue(r["phase129_coverage_update_builder"]["all_coverage_maintained"])

class TestPhase129GapRegister(unittest.TestCase):
    def test_blockers_retained(self):
        r=build_gap_register()
        self.assertTrue(r["phase129_gap_register"]["300394_retained"])
        self.assertTrue(r["phase129_gap_register"]["688041_retained"])

class TestPhase129IntegrationUpdate(unittest.TestCase):
    def test_phases_updated(self):
        r=build_integration_update()
        self.assertIn("phase128",r["phase129_integration_update"]["phases_updated"])

class TestPhase129FallbackBoard(unittest.TestCase):
    def test_not_trade(self):
        r=build_fallback_board()
        self.assertTrue(r["phase129_fallback_board"]["not_trade_board"])

class TestPhase129FallbackBrief(unittest.TestCase):
    def test_has_content(self):
        md=build_fallback_brief_md()
        self.assertIn("Official Source",md)

class TestPhase129FallbackMemory(unittest.TestCase):
    def test_gitignored(self):
        self.assertTrue(build_fallback_memory()["phase129_fallback_memory"]["gitignored"])

class TestPhase129CannotConcludeGuard(unittest.TestCase):
    def test_pass(self):
        r=run_cannot_conclude_guard()
        self.assertEqual(r["phase129_cannot_conclude_guard"]["overall"],"pass")
        self.assertEqual(r["phase129_cannot_conclude_guard"]["violations"],0)

class TestPhase129BacklogUpdate(unittest.TestCase):
    def test_next_phase(self):
        self.assertIn("phase130",build_backlog_update()["phase129_backlog_update"]["next_phase"])

class TestPhase129RegressionGate(unittest.TestCase):
    def test_phase128_regression(self):
        from smr_phase128_cannot_conclude_guard import run_cannot_conclude_guard as g128
        self.assertEqual(g128()["phase128_cannot_conclude_guard"]["overall"],"pass")
    def test_phase127_regression(self):
        from smr_phase127_guard import run_guard
        self.assertEqual(run_guard()["phase127_guard"]["overall"],"pass")

if __name__=="__main__":
    unittest.main()
