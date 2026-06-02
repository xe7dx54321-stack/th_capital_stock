import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
class T117Cfg(unittest.TestCase):
    def test_load(self):from smr_phase117_config import load_config;self.assertEqual(load_config()["phase"],"phase117")
class T117Domain(unittest.TestCase):
    def test_domains(self):from smr_phase117_domain_registry import build_domain_registry;r=build_domain_registry();self.assertTrue(r["phase117_domain_registry"]["total"]>=7)
class T117Steps(unittest.TestCase):
    def test_steps(self):from smr_phase117_step_registry import build_step_registry;r=build_step_registry();self.assertTrue(r["phase117_step_registry"]["total"]>=5)
class T117Deps(unittest.TestCase):
    def test_deps(self):from smr_phase117_dependency_checker import check_dependencies;r=check_dependencies();self.assertTrue(r["phase117_dependency_checker"]["master_runner_ready"])
class T117Planner(unittest.TestCase):
    def test_plan(self):from smr_phase117_execution_planner import build_execution_planner;r=build_execution_planner();self.assertTrue(r["phase117_execution_planner"]["research_only"])
class T117Adapter(unittest.TestCase):
    def test_adapter(self):from smr_phase117_module_adapter import build_module_adapter;r=build_module_adapter();self.assertTrue(r["phase117_module_adapter"]["all_available"])
class T117State(unittest.TestCase):
    def test_state(self):from smr_phase117_state_aggregator import aggregate_run_states;r=aggregate_run_states();self.assertTrue(r["phase117_state_aggregator"]["all_pass"])
class T117Consistency(unittest.TestCase):
    def test_cc(self):from smr_phase117_consistency_checker import check_consistency;r=check_consistency();self.assertTrue(r["phase117_consistency_checker"]["all_pass"])
class T117Degraded(unittest.TestCase):
    def test_dh(self):from smr_phase117_degraded_handler import build_degraded_handler;r=build_degraded_handler();self.assertFalse(r["phase117_degraded_handler"]["currently_degraded"])
class T117Artifact(unittest.TestCase):
    def test_am(self):from smr_phase117_artifact_manifest import build_artifact_manifest;r=build_artifact_manifest();self.assertTrue(r["phase117_artifact_manifest"]["all_gitignored"])
class T117ActionAgg(unittest.TestCase):
    def test_aq(self):from smr_phase117_action_queue_aggregator import aggregate_action_queues;r=aggregate_action_queues();a=r["phase117_unified_action_queue"];self.assertTrue(a["total_deduped"]>=3);self.assertEqual(a["trade_actions"],0)
class T117Board(unittest.TestCase):
    def test_board(self):from smr_phase117_master_board import build_master_board;r=build_master_board();b=r["phase117_master_board"];self.assertEqual(b["total"],8);self.assertTrue(b["not_trade_board"]);self.assertTrue(b["300394_visible"])
class T117History(unittest.TestCase):
    def test_hw(self):from smr_phase117_history_writer import build_history_writer;r=build_history_writer();self.assertTrue(r["phase117_history_writer"]["gitignored"])
class T117Brief(unittest.TestCase):
    def test_brief(self):from smr_phase117_brief_aggregator import build_unified_brief_md;r=build_unified_brief_md();self.assertIn("NVDA",r);self.assertIn("300394",r)
class T117Guard(unittest.TestCase):
    def test_guard(self):from smr_phase117_cannot_conclude_guard import run_master_guard;r=run_master_guard();self.assertEqual(r["phase117_guard"]["overall"],"pass");self.assertEqual(r["phase117_guard"]["violations"],0)
class T117Backlog(unittest.TestCase):
    def test_bl(self):from smr_phase117_backlog_update import build_backlog_update;r=build_backlog_update();self.assertIn("phase118",r["phase117_backlog"]["next_phase_recommendation"])
class T117Dash(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase117_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase117")
        finally:sys.argv=old
class T117Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase117_master_daily_runner import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase117_pipeline"]
            self.assertTrue(d["all_modules_pass"]);self.assertEqual(d["paper_order_created"],0)
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase117_master_daily_runner import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase117_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertEqual(d["violations"],0)
        finally:sys.argv=old
    def test_skip(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase117_master_daily_runner import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase117_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertTrue(d["tickers"]>=6)
        finally:sys.argv=old
if __name__=="__main__":unittest.main()
