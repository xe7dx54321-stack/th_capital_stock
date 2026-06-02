import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
class T120Cfg(unittest.TestCase):
    def test_load(self):from smr_phase120_config import load_config;self.assertEqual(load_config()["phase"],"phase120")
class T120Domain(unittest.TestCase):
    def test_domains(self):from smr_phase120_domain_registry import build_domain_registry;r=build_domain_registry();self.assertTrue(r["phase120_domain_registry"]["total"]>=9)
class T120Summary(unittest.TestCase):
    def test_sm(self):from smr_phase120_summary_loader import load_phase_summaries;r=load_phase_summaries();self.assertTrue(r["phase120_summary_loader"]["total_phases"]>=8)
class T120Capability(unittest.TestCase):
    def test_cm(self):from smr_phase120_capability_map import build_capability_map;r=build_capability_map();self.assertTrue(r["phase120_capability_map"]["all_deployed"])
class T120Workflow(unittest.TestCase):
    def test_wm(self):from smr_phase120_workflow_map import build_daily_workflow_map;r=build_daily_workflow_map();self.assertTrue(r["phase120_workflow_map"]["all_not_trade"])
class T120Artifact(unittest.TestCase):
    def test_ai(self):from smr_phase120_artifact_index import build_artifact_index;r=build_artifact_index();self.assertTrue(r["phase120_artifact_index"]["total_reports"]>=7)
class T120Command(unittest.TestCase):
    def test_ci(self):from smr_phase120_command_index import build_command_index;r=build_command_index();self.assertTrue(r["phase120_command_index"]["total"]>=5)
class T120Gap(unittest.TestCase):
    def test_gr(self):from smr_phase120_gap_register import build_gap_register;r=build_gap_register();self.assertTrue(r["phase120_gap_register"]["all_known"])
class T120Safety(unittest.TestCase):
    def test_sb(self):from smr_phase120_safety_boundary import build_safety_boundary_summary;r=build_safety_boundary_summary();self.assertTrue(r["phase120_safety_boundary"]["all_enforced"])
class T120Retro(unittest.TestCase):
    def test_ret(self):from smr_phase120_retrospective import build_phase_retrospective;r=build_phase_retrospective();self.assertTrue(r["phase120_retrospective"]["total"]>=4)
class T120Acceptance(unittest.TestCase):
    def test_ae(self):from smr_phase120_acceptance_evidence import build_acceptance_evidence;r=build_acceptance_evidence();self.assertTrue(r["phase120_acceptance_evidence"]["project_accepted"])
class T120Roadmap(unittest.TestCase):
    def test_rm(self):from smr_phase120_roadmap_planner import plan_next_roadmap;r=plan_next_roadmap();self.assertIn("phase121",r["phase120_roadmap"]["next_immediate"])
class T120Maintenance(unittest.TestCase):
    def test_mc(self):from smr_phase120_maintenance_checklist import build_maintenance_checklist;r=build_maintenance_checklist();self.assertTrue(r["phase120_maintenance_checklist"]["total"]>=4)
class T120Board(unittest.TestCase):
    def test_board(self):from smr_phase120_closeout_board import build_closeout_board;r=build_closeout_board();b=r["phase120_closeout_board"];self.assertTrue(b["not_trade_board"])
class T120Brief(unittest.TestCase):
    def test_brief(self):from smr_phase120_closeout_brief import build_closeout_brief_md;r=build_closeout_brief_md();self.assertIn("97",r);self.assertIn("300394",r)
class T120Memory(unittest.TestCase):
    def test_mw(self):from smr_phase120_memory_writer import build_memory_writer;r=build_memory_writer();self.assertTrue(r["phase120_memory_writer"]["gitignored"])
class T120Guard(unittest.TestCase):
    def test_guard(self):from smr_phase120_cannot_conclude_guard import run_closeout_guard;r=run_closeout_guard();self.assertEqual(r["phase120_guard"]["overall"],"pass");self.assertEqual(r["phase120_guard"]["violations"],0)
class T120Backlog(unittest.TestCase):
    def test_bl(self):from smr_phase120_backlog_update import build_backlog_update;r=build_backlog_update();self.assertIn("phase121",r["phase120_backlog"]["next_phase_recommendation"])
class T120Dash(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase120_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase120");self.assertTrue(d["project_accepted"])
        finally:sys.argv=old
class T120Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase120_project_closeout import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase120_pipeline"]
            self.assertTrue(d["project_accepted"]);self.assertEqual(d["paper_order_created"],0)
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase120_project_closeout import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase120_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertEqual(d["final_status"],"closeout_complete_system_operational")
        finally:sys.argv=old
    def test_skip(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase120_project_closeout import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase120_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertTrue(d["safety_boundaries_enforced"])
        finally:sys.argv=old
if __name__=="__main__":unittest.main()
