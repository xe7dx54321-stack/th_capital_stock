import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
class T118Cfg(unittest.TestCase):
    def test_load(self):from smr_phase118_config import load_config;self.assertEqual(load_config()["phase"],"phase118")
class T118Domain(unittest.TestCase):
    def test_domains(self):from smr_phase118_domain_registry import build_domain_registry;r=build_domain_registry();self.assertTrue(r["phase118_domain_registry"]["total"]>=10)
class T118Health(unittest.TestCase):
    def test_health(self):from smr_phase117_health_checker import check_master_runner_health;r=check_master_runner_health();self.assertTrue(r["phase118_master_health"]["master_healthy"])
class T118Modules(unittest.TestCase):
    def test_ma(self):from smr_phase118_module_availability import check_module_availability;r=check_module_availability();self.assertTrue(r["phase118_module_availability"]["all_available"])
class T118Artifact(unittest.TestCase):
    def test_ai(self):from smr_phase118_artifact_integrity import check_artifact_integrity;r=check_artifact_integrity();self.assertTrue(r["phase118_artifact_integrity"]["all_ok"])
class T118Freshness(unittest.TestCase):
    def test_df(self):from smr_phase118_data_freshness import check_data_freshness;r=check_data_freshness();self.assertEqual(r["phase118_data_freshness"]["blocked_expected"],1)
class T118Blocker(unittest.TestCase):
    def test_bv(self):from smr_phase118_blocker_visibility import check_blocker_visibility;r=check_blocker_visibility();self.assertTrue(r["phase118_blocker_visibility"]["all_visible"])
class T118Path(unittest.TestCase):
    def test_gp(self):from smr_phase118_generated_path_checker import check_generated_paths;r=check_generated_paths();self.assertTrue(r["phase118_generated_path_checker"]["all_gitignored"])
class T118Latency(unittest.TestCase):
    def test_lt(self):from smr_phase118_latency_monitor import check_latency;r=check_latency();self.assertTrue(r["phase118_latency_monitor"]["all_normal"])
class T118Diagnostics(unittest.TestCase):
    def test_fd(self):from smr_phase118_failure_diagnostics import build_failure_diagnostics;r=build_failure_diagnostics();self.assertTrue(r["phase118_failure_diagnostics"]["no_failures_detected"])
class T118Degraded(unittest.TestCase):
    def test_dn(self):from smr_phase118_degraded_normalizer import build_degraded_normalizer;r=build_degraded_normalizer();self.assertTrue(r["phase118_degraded_normalizer"]["all_not_trade"])
class T118Recovery(unittest.TestCase):
    def test_rc(self):from smr_phase118_recovery_builder import build_recovery_recommendations;r=build_recovery_recommendations();self.assertTrue(r["phase118_recovery_builder"]["all_not_trade"])
class T118Scorecard(unittest.TestCase):
    def test_sc(self):from smr_phase118_reliability_scorecard import build_reliability_scorecard;r=build_reliability_scorecard();self.assertTrue(r["phase118_reliability_scorecard"]["above_threshold"])
class T118HealthBoard(unittest.TestCase):
    def test_board(self):from smr_phase118_health_board import build_health_board;r=build_health_board();b=r["phase118_health_board"];self.assertTrue(b["not_trade_board"]);self.assertTrue(b["300394_visible"])
class T118History(unittest.TestCase):
    def test_hw(self):from smr_phase118_health_history import build_health_history_writer;r=build_health_history_writer();self.assertTrue(r["phase118_health_history"]["gitignored"])
class T118Brief(unittest.TestCase):
    def test_brief(self):from smr_phase118_health_brief import build_health_brief_md;r=build_health_brief_md();self.assertIn("97",r);self.assertIn("300394",r)
class T118Guard(unittest.TestCase):
    def test_guard(self):from smr_phase118_cannot_conclude_guard import run_health_guard;r=run_health_guard();self.assertEqual(r["phase118_guard"]["overall"],"pass");self.assertEqual(r["phase118_guard"]["violations"],0)
class T118Backlog(unittest.TestCase):
    def test_bl(self):from smr_phase118_backlog_update import build_backlog_update;r=build_backlog_update();self.assertIn("phase119",r["phase118_backlog"]["next_phase_recommendation"])
class T118Dash(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase118_dashboard import main as dm
        old=sys.argv[:]
        try:
            sys.argv=["d.py","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase118");self.assertTrue(d["above_threshold"])
        finally:sys.argv=old
class T118Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase118_system_health import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase118_pipeline"]
            self.assertTrue(d["master_healthy"]);self.assertEqual(d["paper_order_created"],0)
        finally:sys.argv=old
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase118_system_health import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase118_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertTrue(d["above_threshold"])
        finally:sys.argv=old
    def test_skip(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase118_system_health import main as rm
        old=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"];buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase118_pipeline"]
            self.assertEqual(d["guard"],"pass");self.assertTrue(d["modules_available"])
        finally:sys.argv=old
if __name__=="__main__":unittest.main()
