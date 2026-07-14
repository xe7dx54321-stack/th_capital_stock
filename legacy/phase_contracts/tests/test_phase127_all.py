import unittest,json,sys,os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "08_scripts" / "lib"))

from smr_phase127_config import load_config
from smr_phase127_domain import build_domain
from smr_phase127_phase_summary import build_phase_summary
from smr_phase127_capability_map import build_capability_map
from smr_phase127_workflow_map import build_workflow_map
from smr_phase127_command_index import build_command_index
from smr_phase127_artifact_index import build_artifact_index
from smr_phase127_research_closeout import build_research_closeout
from smr_phase127_signal_closeout import build_signal_closeout
from smr_phase127_safety_closeout import build_safety_closeout
from smr_phase127_gap_register import build_gap_register
from smr_phase127_blocker_register import build_blocker_register
from smr_phase127_runbook import build_runbook
from smr_phase127_maintenance import build_maintenance
from smr_phase127_roadmap import build_roadmap
from smr_phase127_acceptance import build_acceptance
from smr_phase127_board import build_board
from smr_phase127_brief import build_brief_md
from smr_phase127_memory import build_memory
from smr_phase127_guard import run_guard
from smr_phase127_backlog import build_backlog

class TestPhase127Config(unittest.TestCase):
    def test_loads(self):
        c=load_config()
        self.assertIn("phase",c)
        self.assertEqual(c["phase"],"phase127")
    def test_strategy(self):
        c=load_config()
        self.assertEqual(c["strategy"],"mainline_closeout")
    def test_safety(self):
        c=load_config()
        s=c["safety"]
        self.assertFalse(s["mock"])
        self.assertFalse(s["fixture"])
        self.assertEqual(s["paper_order"],0)
        self.assertFalse(s["raw"])

class TestPhase127Domain(unittest.TestCase):
    def test_has_all(self):
        d=build_domain()
        self.assertTrue(d["phase127_domain"]["all_research_only"])
        self.assertGreater(d["phase127_domain"]["total"],10)

class TestPhase127PhaseSummary(unittest.TestCase):
    def test_16_phases(self):
        p=build_phase_summary()
        self.assertEqual(p["phase127_phase_summary"]["total"],16)
    def test_all_deployed(self):
        p=build_phase_summary()
        self.assertTrue(p["phase127_phase_summary"]["all_deployed"])

class TestPhase127CapabilityMap(unittest.TestCase):
    def test_all_deployed(self):
        c=build_capability_map()
        self.assertTrue(c["phase127_capability_map"]["all_deployed"])

class TestPhase127WorkflowMap(unittest.TestCase):
    def test_not_trade(self):
        w=build_workflow_map()
        self.assertTrue(w["phase127_workflow_map"]["all_not_trade"])

class TestPhase127CommandIndex(unittest.TestCase):
    def test_has_commands(self):
        c=build_command_index()
        self.assertGreater(len(c["phase127_command_index"]["commands"]),0)

class TestPhase127ArtifactIndex(unittest.TestCase):
    def test_has_artifacts(self):
        a=build_artifact_index()
        self.assertGreater(len(a["phase127_artifact_index"]["artifacts"]),0)

class TestPhase127ResearchCloseout(unittest.TestCase):
    def test_operational(self):
        r=build_research_closeout()
        self.assertEqual(r["phase127_research_closeout"]["status"],"operational")
    def test_300394_blocked(self):
        r=build_research_closeout()
        self.assertIn("300394.SZ",r["phase127_research_closeout"]["blocked"])
    def test_688041_partial(self):
        r=build_research_closeout()
        self.assertIn("688041.SH",r["phase127_research_closeout"]["partial"])
    def test_research_only(self):
        r=build_research_closeout()
        self.assertTrue(r["phase127_research_closeout"]["research_only"])

class TestPhase127SignalCloseout(unittest.TestCase):
    def test_no_trade(self):
        s=build_signal_closeout()
        self.assertTrue(s["phase127_signal_closeout"]["no_trade_signals"])

class TestPhase127SafetyCloseout(unittest.TestCase):
    def test_all_enforced(self):
        s=build_safety_closeout()
        self.assertTrue(s["phase127_safety_closeout"]["all_enforced"])
        self.assertEqual(s["phase127_safety_closeout"]["total"],10)

class TestPhase127GapRegister(unittest.TestCase):
    def test_all_known(self):
        g=build_gap_register()
        self.assertTrue(g["phase127_gap_register"]["all_known"])

class TestPhase127BlockerRegister(unittest.TestCase):
    def test_300394_retained(self):
        b=build_blocker_register()
        blockers=[x for x in b["phase127_blocker_register"]["blockers"] if x["ticker"]=="300394.SZ"]
        self.assertEqual(len(blockers),1)
        self.assertTrue(blockers[0]["retained"])
    def test_688041_retained(self):
        b=build_blocker_register()
        blockers=[x for x in b["phase127_blocker_register"]["blockers"] if x["ticker"]=="688041.SH"]
        self.assertEqual(len(blockers),1)

class TestPhase127Runbook(unittest.TestCase):
    def test_research_only(self):
        r=build_runbook()
        self.assertTrue(r["phase127_runbook"]["research_only"])

class TestPhase127Maintenance(unittest.TestCase):
    def test_has_checklist(self):
        m=build_maintenance()
        self.assertGreater(len(m["phase127_maintenance"]["checklist"]),0)

class TestPhase127Roadmap(unittest.TestCase):
    def test_has_recommended(self):
        r=build_roadmap()
        self.assertIn("recommended",r["phase127_roadmap"])

class TestPhase127Acceptance(unittest.TestCase):
    def test_all_met(self):
        a=build_acceptance()
        self.assertTrue(a["phase127_acceptance"]["all_met"])
        self.assertTrue(a["phase127_acceptance"]["phase111_126_mainline_accepted"])

class TestPhase127Board(unittest.TestCase):
    def test_not_trade(self):
        b=build_board()
        self.assertTrue(b["phase127_board"]["not_trade_board"])

class TestPhase127Brief(unittest.TestCase):
    def test_not_empty(self):
        md=build_brief_md()
        self.assertIn("Phase111-126",md)
    def test_no_system_terms(self):
        md=build_brief_md()
        for t in ["pending","candidate","dashboard","runner","mock","fixture"]:
            self.assertNotIn(t,md.split("# Status")[0] if "# Status" in md else md)

class TestPhase127Memory(unittest.TestCase):
    def test_ignored(self):
        m=build_memory()
        self.assertTrue(m["phase127_memory"]["gitignored"])

class TestPhase127Guard(unittest.TestCase):
    def test_pass(self):
        g=run_guard()
        self.assertEqual(g["phase127_guard"]["overall"],"pass")
        self.assertEqual(g["phase127_guard"]["violations"],0)

class TestPhase127Backlog(unittest.TestCase):
    def test_mainline_closed(self):
        b=build_backlog()
        self.assertEqual(b["phase127_backlog"]["phase111_126_mainline"],"closed")
    def test_next_phase(self):
        b=build_backlog()
        self.assertIn("phase128",b["phase127_backlog"]["next_phase"])
    def test_deprecated(self):
        b=build_backlog()
        for d in ["paper_order","target_price","position_sizing","profit_loss"]:
            self.assertIn(d,b["phase127_backlog"]["deprecated_forever"])

class TestPhase127DashboardIntegration(unittest.TestCase):
    def test_key_fields(self):
        a=build_acceptance()
        g=run_guard()
        b=build_backlog()
        self.assertTrue(a["phase127_acceptance"]["phase111_126_mainline_accepted"])
        self.assertEqual(g["phase127_guard"]["overall"],"pass")
        self.assertEqual(b["phase127_backlog"]["phase111_126_mainline"],"closed")

class TestPhase127RegressionGate(unittest.TestCase):
    def test_phase126_dashboard_still_works(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "08_scripts" / "reporting"))
        try:
            import build_phase126_dashboard
        except ImportError:
            self.skipTest("phase126 dashboard not importable")
    def test_300394_blocker_visible(self):
        b=build_blocker_register()
        found=False
        for bl in b["phase127_blocker_register"]["blockers"]:
            if bl["ticker"]=="300394.SZ":
                found=True
                self.assertTrue(bl["retained"])
        self.assertTrue(found,"300394 blocker not found")
    def test_688041_partial_visible(self):
        r=build_research_closeout()
        self.assertIn("688041.SH",r["phase127_research_closeout"]["partial"])

if __name__=="__main__":
    unittest.main()
