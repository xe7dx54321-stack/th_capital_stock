import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

class TestPhase99Config(unittest.TestCase):
    def test_load(self):
        from smr_phase99_config import load_config
        self.assertEqual(load_config()["phase"],"phase99")
    def test_recovery_enabled(self):
        from smr_phase99_config import is_recovery_enabled
        self.assertTrue(is_recovery_enabled())
    def test_registry(self):
        from smr_phase99_config import get_failover_registry
        self.assertEqual(len(get_failover_registry()),7)
    def test_history_ignored(self):
        from smr_phase99_config import load_config
        self.assertTrue(load_config()["recovery_history"]["gitignored"])
    def test_no_mock(self):
        from smr_phase99_config import load_config
        self.assertFalse(load_config()["safety"]["mock_allowed"])

class TestPhase99FailoverRegistry(unittest.TestCase):
    def test_registry(self):
        from smr_phase99_source_failover_registry import build_failover_registry
        r=build_failover_registry()
        self.assertEqual(r["phase99_failover_registry"]["total_sources"],7)
        self.assertEqual(r["phase99_failover_registry"]["blocked_sources"],3)

class TestPhase99FallbackSelector(unittest.TestCase):
    def test_selector(self):
        from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
        from smr_phase99_fallback_source_selector import select_fallback_sources
        hb=run_heartbeat_probe("execute")
        r=select_fallback_sources(hb)
        self.assertGreater(r["phase99_fallback_selector"]["fallback_needed"],0)

class TestPhase99PrimaryRetry(unittest.TestCase):
    def test_dry(self):
        from smr_phase99_primary_source_retry import run_primary_retry
        r=run_primary_retry("dry-run")
        self.assertEqual(len(r["phase99_primary_retry"]["results"]),7)
    def test_skip_network(self):
        from smr_phase99_primary_source_retry import run_primary_retry
        r=run_primary_retry("skip-network")
        self.assertGreater(r["phase99_primary_retry"]["retry_failed"],0)

class TestPhase99FallbackExecution(unittest.TestCase):
    def test_fallback(self):
        from smr_phase99_primary_source_retry import run_primary_retry
        from smr_phase99_fallback_execution import run_fallback_execution
        retry=run_primary_retry("execute")
        r=run_fallback_execution(retry,"execute")
        self.assertGreater(r["phase99_fallback_execution"]["fallback_recovered"],0)

class TestPhase99DegradedParser(unittest.TestCase):
    def test_degraded(self):
        from smr_phase99_degraded_parser import run_degraded_parser
        r=run_degraded_parser("execute")
        self.assertGreater(r["phase99_degraded_parser"]["degraded_recovered"],0)

class TestPhase99FieldMapping(unittest.TestCase):
    def test_mapping(self):
        from smr_phase99_alternative_field_mapping import run_alternative_field_mapping
        r=run_alternative_field_mapping("execute")
        self.assertGreater(r["phase99_alternative_field_mapping"]["fields_recovered"],0)

class TestPhase99StaleRefresh(unittest.TestCase):
    def test_stale(self):
        from smr_phase99_stale_source_refresh import run_stale_refresh
        r=run_stale_refresh("execute")
        self.assertGreater(r["phase99_stale_refresh"]["stale_refresh_recovered"],0)

class TestPhase99BlockedReplacement(unittest.TestCase):
    def test_replacement(self):
        from smr_phase99_blocked_source_replacement import run_blocked_replacement
        r=run_blocked_replacement("execute")
        self.assertGreater(r["phase99_blocked_replacement"]["replacement_recovered"],0)

class TestPhase99Classifier(unittest.TestCase):
    def test_classify(self):
        from smr_phase99_primary_source_retry import run_primary_retry
        from smr_phase99_fallback_execution import run_fallback_execution
        from smr_phase99_degraded_parser import run_degraded_parser
        from smr_phase99_alternative_field_mapping import run_alternative_field_mapping
        from smr_phase99_stale_source_refresh import run_stale_refresh
        from smr_phase99_blocked_source_replacement import run_blocked_replacement
        from smr_phase99_recovery_result_classifier import classify_recovery_results
        retry=run_primary_retry("execute");fallback=run_fallback_execution(retry,"execute")
        degraded=run_degraded_parser("execute");fmap=run_alternative_field_mapping("execute")
        stale=run_stale_refresh("execute");repl=run_blocked_replacement("execute")
        r=classify_recovery_results(retry,fallback,degraded,fmap,stale,repl)
        self.assertGreater(r["phase99_recovery_classifier"]["recovered"],0)

class TestPhase99RecoveryHistory(unittest.TestCase):
    def test_dry(self):
        from smr_phase99_primary_source_retry import run_primary_retry
        from smr_phase99_fallback_execution import run_fallback_execution
        from smr_phase99_degraded_parser import run_degraded_parser
        from smr_phase99_alternative_field_mapping import run_alternative_field_mapping
        from smr_phase99_stale_source_refresh import run_stale_refresh
        from smr_phase99_blocked_source_replacement import run_blocked_replacement
        from smr_phase99_recovery_history import write_recovery_history
        retry=run_primary_retry("execute");fallback=run_fallback_execution(retry,"execute")
        degraded=run_degraded_parser("execute");fmap=run_alternative_field_mapping("execute")
        stale=run_stale_refresh("execute");repl=run_blocked_replacement("execute")
        r=write_recovery_history(retry,fallback,degraded,fmap,stale,repl,"dry-run")
        self.assertTrue(r["phase99_recovery_history"]["recovery_history_path_ignored"])
    def test_execute(self):
        from smr_phase99_primary_source_retry import run_primary_retry
        from smr_phase99_fallback_execution import run_fallback_execution
        from smr_phase99_degraded_parser import run_degraded_parser
        from smr_phase99_alternative_field_mapping import run_alternative_field_mapping
        from smr_phase99_stale_source_refresh import run_stale_refresh
        from smr_phase99_blocked_source_replacement import run_blocked_replacement
        from smr_phase99_recovery_history import write_recovery_history
        retry=run_primary_retry("execute");fallback=run_fallback_execution(retry,"execute")
        degraded=run_degraded_parser("execute");fmap=run_alternative_field_mapping("execute")
        stale=run_stale_refresh("execute");repl=run_blocked_replacement("execute")
        r=write_recovery_history(retry,fallback,degraded,fmap,stale,repl,"execute")
        self.assertGreater(r["phase99_recovery_history"]["entries_written"],0)

class TestPhase99IncidentUpdate(unittest.TestCase):
    def test_update(self):
        from smr_phase99_primary_source_retry import run_primary_retry
        from smr_phase99_fallback_execution import run_fallback_execution
        from smr_phase99_degraded_parser import run_degraded_parser
        from smr_phase99_alternative_field_mapping import run_alternative_field_mapping
        from smr_phase99_stale_source_refresh import run_stale_refresh
        from smr_phase99_blocked_source_replacement import run_blocked_replacement
        from smr_phase99_recovery_result_classifier import classify_recovery_results
        from smr_phase99_source_incident_update import update_incidents
        retry=run_primary_retry("execute");fallback=run_fallback_execution(retry,"execute")
        degraded=run_degraded_parser("execute");fmap=run_alternative_field_mapping("execute")
        stale=run_stale_refresh("execute");repl=run_blocked_replacement("execute")
        cl=classify_recovery_results(retry,fallback,degraded,fmap,stale,repl)
        r=update_incidents(cl)
        self.assertGreater(r["phase99_incident_update"]["incidents_updated"],0)

class TestPhase99HealthRefresh(unittest.TestCase):
    def test_health(self):
        from smr_phase99_primary_source_retry import run_primary_retry
        from smr_phase99_fallback_execution import run_fallback_execution
        from smr_phase99_degraded_parser import run_degraded_parser
        from smr_phase99_alternative_field_mapping import run_alternative_field_mapping
        from smr_phase99_stale_source_refresh import run_stale_refresh
        from smr_phase99_blocked_source_replacement import run_blocked_replacement
        from smr_phase99_recovery_result_classifier import classify_recovery_results
        from smr_phase99_recovered_source_health import refresh_recovered_health
        retry=run_primary_retry("execute");fallback=run_fallback_execution(retry,"execute")
        degraded=run_degraded_parser("execute");fmap=run_alternative_field_mapping("execute")
        stale=run_stale_refresh("execute");repl=run_blocked_replacement("execute")
        cl=classify_recovery_results(retry,fallback,degraded,fmap,stale,repl)
        r=refresh_recovered_health(cl,fallback)
        self.assertGreater(r["phase99_recovered_health"]["health_improved"],0)

class TestPhase99QualityGate(unittest.TestCase):
    def test_gate(self):
        from smr_phase99_primary_source_retry import run_primary_retry
        from smr_phase99_fallback_execution import run_fallback_execution
        from smr_phase99_degraded_parser import run_degraded_parser
        from smr_phase99_alternative_field_mapping import run_alternative_field_mapping
        from smr_phase99_stale_source_refresh import run_stale_refresh
        from smr_phase99_blocked_source_replacement import run_blocked_replacement
        from smr_phase99_recovery_quality_gate import run_recovery_quality_gate
        retry=run_primary_retry("execute");fallback=run_fallback_execution(retry,"execute")
        degraded=run_degraded_parser("execute");fmap=run_alternative_field_mapping("execute")
        stale=run_stale_refresh("execute");repl=run_blocked_replacement("execute")
        r=run_recovery_quality_gate(retry,fallback,degraded,fmap,stale,repl)
        self.assertEqual(r["phase99_recovery_quality_gate"]["overall"],"pass")

class TestPhase99Guard(unittest.TestCase):
    def test_guard(self):
        from smr_phase99_primary_source_retry import run_primary_retry
        from smr_phase99_fallback_execution import run_fallback_execution
        from smr_phase99_degraded_parser import run_degraded_parser
        from smr_phase99_alternative_field_mapping import run_alternative_field_mapping
        from smr_phase99_stale_source_refresh import run_stale_refresh
        from smr_phase99_blocked_source_replacement import run_blocked_replacement
        from smr_phase99_recovery_result_classifier import classify_recovery_results
        from smr_phase99_recovery_cannot_conclude_guard import run_recovery_guard
        retry=run_primary_retry("execute");fallback=run_fallback_execution(retry,"execute")
        degraded=run_degraded_parser("execute");fmap=run_alternative_field_mapping("execute")
        stale=run_stale_refresh("execute");repl=run_blocked_replacement("execute")
        cl=classify_recovery_results(retry,fallback,degraded,fmap,stale,repl)
        r=run_recovery_guard(cl)
        self.assertEqual(r["phase99_recovery_guard"]["overall"],"fail")

class TestPhase99Backlog(unittest.TestCase):
    def test_backlog(self):
        from smr_phase99_backlog_update import build_backlog_update
        r=build_backlog_update()
        self.assertGreaterEqual(r["phase99_backlog_update"]["items"],8)
    def test_phase100(self):
        from smr_phase99_backlog_update import build_backlog_update
        self.assertIn("phase100_recommendation",build_backlog_update()["phase99_backlog_update"])

class TestPhase99Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase99_self_healing_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase99_pipeline"]
            self.assertEqual(d["mode"],"dry-run")
            self.assertTrue(d["recovery_history_path_ignored"])
        finally:sys.argv=o
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase99_self_healing_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase99_pipeline"]
            self.assertEqual(d["mode"],"execute")
            self.assertGreater(d["total_recovered"],0)
        finally:sys.argv=o
    def test_skip_network(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase99_self_healing_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase99_pipeline"]
            self.assertEqual(d["mode"],"skip-network")
        finally:sys.argv=o
    def test_no_pending(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase99_self_healing_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            p=json.loads(buf.getvalue())["phase99_pipeline"]
            self.assertEqual(p["pending_created"],0)
            self.assertFalse(p["mock_used"])
        finally:sys.argv=o

class TestPhase99Dashboard(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase99_self_healing_dashboard import main as dm
        o=sys.argv[:]
        try:
            sys.argv=["d.py","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["tickers_checked"],8)
            self.assertFalse(d["mock_used"])
            self.assertEqual(d["pending_created"],0)
        finally:sys.argv=o

if __name__=="__main__":
    unittest.main()
