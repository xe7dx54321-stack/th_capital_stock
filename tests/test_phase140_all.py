import unittest,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
from smr_phase140_config import load_config
from smr_phase140_domain_registry import build_domain_registry
from smr_phase140_module_regression_matrix import build_module_regression_matrix
from smr_phase140_artifact_integrity_checker import build_artifact_integrity_checker
from smr_phase140_config_consistency_auditor import build_config_consistency_auditor
from smr_phase140_generated_path_auditor import build_generated_path_auditor
from smr_phase140_safety_boundary_auditor import build_safety_boundary_auditor
from smr_phase140_degradation_policy_validator import build_degradation_policy_validator
from smr_phase140_known_blocker_retention_checker import build_known_blocker_retention_checker
from smr_phase140_source_limitation_visibility_checker import build_source_limitation_visibility_checker
from smr_phase140_operational_reliability_scorecard import build_operational_reliability_scorecard
from smr_phase140_recovery_recommendation_builder import build_recovery_recommendation
from smr_phase140_maintenance_checklist_builder import build_maintenance_checklist
from smr_phase140_quality_gate import run_quality_gate
from smr_phase140_cannot_conclude_guard import run_cannot_conclude_guard
from smr_phase140_backlog_update import build_backlog_update

class T140Config(unittest.TestCase):
    def test_loads(self): self.assertEqual(load_config()["phase"],"phase140")
    def test_research(self): self.assertTrue(load_config()["research_only"])
class T140Domain(unittest.TestCase):
    def test_count(self): self.assertGreater(build_domain_registry()["phase140_domain_registry"]["total"],18)
class T140Regression(unittest.TestCase):
    def test_matrix(self): self.assertTrue(build_module_regression_matrix()["phase140_module_regression_matrix"]["matrix"]["all_pass"])
class T140Artifact(unittest.TestCase):
    def test_integrity(self): self.assertTrue(build_artifact_integrity_checker()["phase140_artifact_integrity_checker"]["all_integrity_pass"])
class T140ConfigAudit(unittest.TestCase):
    def test_pass(self): self.assertTrue(build_config_consistency_auditor()["phase140_config_consistency_auditor"]["pass"])
class T140PathAudit(unittest.TestCase):
    def test_pass(self): self.assertTrue(build_generated_path_auditor()["phase140_generated_path_auditor"]["pass"])
class T140SafetyAudit(unittest.TestCase):
    def test_pass(self): self.assertTrue(build_safety_boundary_auditor()["phase140_safety_boundary_auditor"]["pass"])
class T140Degradation(unittest.TestCase):
    def test_pass(self): self.assertTrue(build_degradation_policy_validator()["phase140_degradation_policy_validator"]["pass"])
class T140Blocker(unittest.TestCase):
    def test_retained(self): self.assertTrue(build_known_blocker_retention_checker()["phase140_known_blocker_retention_checker"]["pass"])
class T140SourceLimitation(unittest.TestCase):
    def test_pass(self): self.assertTrue(build_source_limitation_visibility_checker()["phase140_source_limitation_visibility_checker"]["pass"])
class T140Scorecard(unittest.TestCase):
    def test_score(self): self.assertEqual(build_operational_reliability_scorecard()["phase140_operational_reliability_scorecard"]["scorecard"]["overall_score"],100)
class T140Recovery(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_recovery_recommendation()["phase140_recovery_recommendation_builder"]["ready"])
class T140Maintenance(unittest.TestCase):
    def test_ready(self): self.assertTrue(build_maintenance_checklist()["phase140_maintenance_checklist_builder"]["ready"])
class T140Quality(unittest.TestCase):
    def test_pass(self): self.assertEqual(run_quality_gate()["phase140_quality_gate"]["overall"],"pass")
class T140Guard(unittest.TestCase):
    def test_pass(self): self.assertEqual(run_cannot_conclude_guard()["phase140_cannot_conclude_guard"]["overall"],"pass")
class T140Backlog(unittest.TestCase):
    def test_deployed(self): self.assertIn("hardening",build_backlog_update()["phase140_backlog_update"]["phase140_status"])
if __name__=="__main__":unittest.main()
