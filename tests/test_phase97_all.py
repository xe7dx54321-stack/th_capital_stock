import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

class TestPhase97Config(unittest.TestCase):
    def test_load(self):
        from smr_phase97_config import load_config
        self.assertEqual(load_config()["phase"],"phase97")
    def test_phase_key(self):
        from smr_phase97_config import load_config
        self.assertEqual(load_config()["strategy"],"automated_db_refresh_and_incremental_hard_data_update")
    def test_db_ignored(self):
        from smr_phase97_config import load_config
        self.assertTrue(load_config()["db"]["all_gitignored"])
    def test_no_mock(self):
        from smr_phase97_config import load_config
        self.assertFalse(load_config()["safety"]["mock_allowed"])
    def test_dedup_enabled(self):
        from smr_phase97_config import is_dedup_enabled
        self.assertTrue(is_dedup_enabled())
    def test_stale_days(self):
        from smr_phase97_config import get_stale_days
        self.assertEqual(get_stale_days(),[7,14,30])

class TestPhase97DBCompatibility(unittest.TestCase):
    def test_compat(self):
        from smr_phase97_phase96_db_compatibility import check_compatibility
        r=check_compatibility()
        self.assertEqual(r["phase97_phase96_db_compatibility"]["overall"],"pass")
    def test_no_mock(self):
        from smr_phase97_phase96_db_compatibility import check_compatibility
        self.assertFalse(check_compatibility()["phase97_phase96_db_compatibility"]["mock_used"])

class TestPhase97SourceRefreshPolicy(unittest.TestCase):
    def test_policy(self):
        from smr_phase97_source_refresh_policy import build_source_refresh_policy
        r=build_source_refresh_policy()
        self.assertEqual(r["phase97_source_refresh_policy"]["sources"],7)
        self.assertGreaterEqual(r["phase97_source_refresh_policy"]["refreshable"],3)
        self.assertGreaterEqual(r["phase97_source_refresh_policy"]["blocked"],3)
    def test_no_mock(self):
        from smr_phase97_source_refresh_policy import build_source_refresh_policy
        self.assertFalse(build_source_refresh_policy()["phase97_source_refresh_policy"]["mock_used"])

class TestPhase97SourceRefreshPlanner(unittest.TestCase):
    def test_dry(self):
        from smr_phase97_source_refresh_planner import build_refresh_plan
        r=build_refresh_plan("dry-run")
        self.assertEqual(r["phase97_source_refresh_plan"]["mode"],"dry-run")
        self.assertEqual(r["phase97_source_refresh_plan"]["total_sources"],7)
    def test_execute(self):
        from smr_phase97_source_refresh_planner import build_refresh_plan
        r=build_refresh_plan("execute")
        self.assertGreaterEqual(r["phase97_source_refresh_plan"]["refresh_count"],3)
    def test_skip_network(self):
        from smr_phase97_source_refresh_planner import build_refresh_plan
        r=build_refresh_plan("skip-network")
        self.assertEqual(r["phase97_source_refresh_plan"]["refresh_count"],0)

class TestPhase97IncrementalLoader(unittest.TestCase):
    def test_dry(self):
        from smr_phase97_incremental_loader import load_incremental_sources
        r=load_incremental_sources("dry-run")
        self.assertEqual(r["phase97_incremental_loader"]["mode"],"dry-run")
        self.assertEqual(r["phase97_incremental_loader"]["new_records_attempted"],0)
    def test_no_mock(self):
        from smr_phase97_incremental_loader import load_incremental_sources
        self.assertFalse(load_incremental_sources()["phase97_incremental_loader"]["mock_used"])

class TestPhase97RecordFingerprint(unittest.TestCase):
    def test_fingerprint(self):
        from smr_phase97_record_fingerprint import fingerprint_record
        r1={"ticker":"NVDA","hard_data_category":"financial","field_name":"revenue","source_phase":"phase92","period":"FY2025"}
        r2={"ticker":"NVDA","hard_data_category":"financial","field_name":"revenue","source_phase":"phase92","period":"FY2025"}
        self.assertEqual(fingerprint_record(r1),fingerprint_record(r2))
    def test_dedup_same(self):
        from smr_phase97_record_fingerprint import dedup_records
        records=[{"ticker":"NVDA","hard_data_category":"financial","field_name":"revenue","source_phase":"phase92","period":"FY2025","as_of_date":"2025-01-01"},{"ticker":"NVDA","hard_data_category":"financial","field_name":"revenue","source_phase":"phase92","period":"FY2025","as_of_date":"2025-01-01"}]
        r=dedup_records(records)
        self.assertEqual(r["phase97_dedup"]["unique_count"],1)
        self.assertEqual(r["phase97_dedup"]["duplicates_removed"],1)
    def test_dedup_no_dup(self):
        from smr_phase97_record_fingerprint import dedup_records
        records=[{"ticker":"NVDA","hard_data_category":"financial","field_name":"revenue","source_phase":"phase92","period":"FY2025"},{"ticker":"AVGO","hard_data_category":"financial","field_name":"revenue","source_phase":"phase92","period":"FY2025"}]
        r=dedup_records(records)
        self.assertEqual(r["phase97_dedup"]["duplicates_removed"],0)

class TestPhase97LifecycleClassifier(unittest.TestCase):
    def test_classify(self):
        from smr_phase97_lifecycle_classifier import classify_lifecycle
        records=[{"ticker":"TEST","hard_data_category":"financial","field_name":"rev","as_of_date":"2099-01-01"}]
        r=classify_lifecycle(records)
        self.assertEqual(r["phase97_lifecycle"]["fresh"],1)
    def test_stale(self):
        from smr_phase97_lifecycle_classifier import classify_lifecycle
        records=[{"ticker":"TEST","hard_data_category":"financial","field_name":"rev","as_of_date":"2020-01-01"}]
        r=classify_lifecycle(records)
        self.assertEqual(r["phase97_lifecycle"]["expired"],1)
    def test_no_date(self):
        from smr_phase97_lifecycle_classifier import classify_lifecycle
        r=classify_lifecycle([{"ticker":"TEST"}])
        self.assertEqual(r["phase97_lifecycle"]["stale"],1)

class TestPhase97DeltaDetector(unittest.TestCase):
    def test_add(self):
        from smr_phase97_delta_detector import detect_deltas
        old=[{"ticker":"A","hard_data_category":"fin","field_name":"r1","field_value":"100"}]
        new=[{"ticker":"A","hard_data_category":"fin","field_name":"r1","field_value":"100"},{"ticker":"B","hard_data_category":"fin","field_name":"r2","field_value":"200"}]
        r=detect_deltas(old,new)
        self.assertEqual(r["phase97_delta"]["added"],1)
        self.assertEqual(r["phase97_delta"]["changed"],0)
    def test_change(self):
        from smr_phase97_delta_detector import detect_deltas
        old=[{"ticker":"A","hard_data_category":"fin","field_name":"r1","field_value":"100"}]
        new=[{"ticker":"A","hard_data_category":"fin","field_name":"r1","field_value":"200"}]
        r=detect_deltas(old,new)
        self.assertEqual(r["phase97_delta"]["changed"],1)
    def test_remove(self):
        from smr_phase97_delta_detector import detect_deltas
        old=[{"ticker":"A","hard_data_category":"fin","field_name":"r1","field_value":"100"}]
        new=[]
        r=detect_deltas(old,new)
        self.assertEqual(r["phase97_delta"]["removed"],1)

class TestPhase97StaleDetector(unittest.TestCase):
    def test_detect(self):
        from smr_phase97_stale_detector import detect_stale_expired
        records=[{"record_id":"t1","ticker":"TEST","field_name":"rev","as_of_date":"2020-01-01"}]
        r=detect_stale_expired(records)
        self.assertEqual(r["phase97_stale_detector"]["expired"],1)
        self.assertEqual(r["phase97_stale_detector"]["valid"],0)
    def test_no_date(self):
        from smr_phase97_stale_detector import detect_stale_expired
        r=detect_stale_expired([{"record_id":"t2","ticker":"TEST"}])
        self.assertEqual(r["phase97_stale_detector"]["stale"],1)

class TestPhase97IncrementalWriter(unittest.TestCase):
    def test_dry(self):
        from smr_phase97_incremental_writer import write_incremental
        r=write_incremental([{"ticker":"TEST","hard_data_category":"fin","record_id":"rid"}],"dry-run")
        self.assertEqual(r["mode"],"dry-run")
        self.assertTrue(r["db_path_ignored"])
    def test_execute(self):
        from smr_phase97_incremental_writer import write_incremental
        r=write_incremental([{"ticker":"TEST","hard_data_category":"fin","record_id":"rid","field_name":"rev","field_value":"100","source_phase":"phase92","period":"FY2025"}],"execute")
        self.assertTrue(r["db_path_ignored"])
        self.assertGreater(r["records_written"],0)

class TestPhase97ManifestVersioning(unittest.TestCase):
    def test_manifest(self):
        from smr_phase97_manifest_versioning import build_manifest_version
        r=build_manifest_version()
        self.assertTrue(r["phase97_manifest_versioning"]["current_manifest"]["all_gitignored"])

class TestPhase97RefreshRunHistory(unittest.TestCase):
    def test_history(self):
        from smr_phase97_refresh_run_history import build_refresh_history
        r=build_refresh_history()
        self.assertTrue(r["phase97_refresh_history"]["history_enabled"])
        self.assertTrue(r["phase97_refresh_history"]["history_path_ignored"])

class TestPhase97RefreshStatusBoard(unittest.TestCase):
    def test_board(self):
        from smr_phase97_source_refresh_planner import build_refresh_plan
        from smr_phase97_refresh_status_board import build_refresh_status_board
        plan=build_refresh_plan("execute")
        delta={"phase97_delta":{"added":1,"changed":0}}
        dedup={"phase97_dedup":{"duplicates_removed":0}}
        r=build_refresh_status_board(plan,delta,dedup)
        self.assertEqual(r["phase97_refresh_status_board"]["sources"],7)
        self.assertGreaterEqual(r["phase97_refresh_status_board"]["refreshed"],3)
        self.assertEqual(r["phase97_refresh_status_board"]["delta_added"],1)

class TestPhase97QualityGate(unittest.TestCase):
    def test_pass(self):
        from smr_phase97_quality_gate import run_refresh_quality_gate
        dedup={"phase97_dedup":{"original_count":2,"unique_count":2}}
        delta={"phase97_delta":{"added":0,"changed":0}}
        wr={"mode":"execute","records_written":1}
        r=run_refresh_quality_gate(dedup,delta,wr)
        self.assertEqual(r["phase97_refresh_quality_gate"]["overall"],"pass")
    def test_checks_count(self):
        from smr_phase97_quality_gate import run_refresh_quality_gate
        d={"phase97_dedup":{"original_count":1,"unique_count":1}}
        dl={"phase97_delta":{"added":0,"changed":0}}
        w={"mode":"dry-run","records_written":0}
        self.assertEqual(len(run_refresh_quality_gate(d,dl,w)["phase97_refresh_quality_gate"]["checks"]),3)

class TestPhase97CannotConcludeGuard(unittest.TestCase):
    def test_pass(self):
        from smr_phase97_cannot_conclude_guard import run_refresh_guard
        delta={"phase97_delta":{"added":0,"changed":0,"added_records":[],"changed_records":[]}}
        r=run_refresh_guard(delta)
        self.assertEqual(r["phase97_refresh_guard"]["overall"],"pass")
    def test_violation(self):
        from smr_phase97_cannot_conclude_guard import run_refresh_guard
        delta={"phase97_delta":{"added":1,"changed":0,"added_records":[{"record_id":"x","data_type":"peer_context_only"}],"changed_records":[]}}
        r=run_refresh_guard(delta)
        self.assertEqual(r["phase97_refresh_guard"]["overall"],"fail")

class TestPhase97BacklogUpdate(unittest.TestCase):
    def test_backlog(self):
        from smr_phase97_backlog_update import build_backlog_update
        r=build_backlog_update()
        self.assertEqual(r["phase97_backlog_update"]["items"],8)
    def test_phase98(self):
        from smr_phase97_backlog_update import build_backlog_update
        r=build_backlog_update()
        self.assertIn("phase98_recommendation",r["phase97_backlog_update"])

class TestPhase97Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase97_automated_db_refresh_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase97_pipeline"]
            self.assertEqual(d["mode"],"dry-run")
            self.assertTrue(d["db_path_ignored"])
        finally:sys.argv=o
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase97_automated_db_refresh_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase97_pipeline"]
            self.assertEqual(d["mode"],"execute")
            self.assertGreater(d["records_written"],0)
        finally:sys.argv=o
    def test_skip_network(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase97_automated_db_refresh_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase97_pipeline"]
            self.assertEqual(d["mode"],"skip-network")
        finally:sys.argv=o
    def test_no_pending(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase97_automated_db_refresh_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            p=json.loads(buf.getvalue())["phase97_pipeline"]
            self.assertEqual(p["pending_created"],0)
            self.assertFalse(p["mock_used"])
        finally:sys.argv=o

class TestPhase97Dashboard(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase97_dashboard import main as dm
        o=sys.argv[:]
        try:
            sys.argv=["d.py","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase97")
            self.assertFalse(d["mock_used"])
            self.assertEqual(d["pending_created"],0)
        finally:sys.argv=o

if __name__=="__main__":
    unittest.main()
