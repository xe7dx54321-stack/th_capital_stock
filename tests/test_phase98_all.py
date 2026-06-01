import unittest, sys, os, json, io, contextlib
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))

class TestPhase98Config(unittest.TestCase):
    def test_load(self):
        from smr_phase98_config import load_config
        self.assertEqual(load_config()["phase"],"phase98")
    def test_sources(self):
        from smr_phase98_config import get_sources_to_monitor
        self.assertEqual(len(get_sources_to_monitor()),7)
    def test_health_levels(self):
        from smr_phase98_config import get_health_levels
        self.assertEqual(len(get_health_levels()),5)
    def test_alerting(self):
        from smr_phase98_config import is_alerting_enabled
        self.assertTrue(is_alerting_enabled())
    def test_external_disabled(self):
        from smr_phase98_config import is_external_notification_enabled
        self.assertFalse(is_external_notification_enabled())
    def test_no_mock(self):
        from smr_phase98_config import load_config
        self.assertFalse(load_config()["safety"]["mock_allowed"])

class TestPhase98SourceHealthRegistry(unittest.TestCase):
    def test_registry(self):
        from smr_phase98_source_health_registry import build_source_health_registry
        r=build_source_health_registry()
        self.assertEqual(r["phase98_source_health_registry"]["sources_monitored"],7)
        self.assertEqual(r["phase98_source_health_registry"]["health_status_summary"]["blocked"],3)

class TestPhase98Heartbeat(unittest.TestCase):
    def test_dry(self):
        from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
        r=run_heartbeat_probe("dry-run")
        self.assertEqual(r["phase98_heartbeat_probe"]["mode"],"dry-run")
        self.assertEqual(r["phase98_heartbeat_probe"]["total_sources"],7)
        self.assertGreater(r["phase98_heartbeat_probe"]["healthy"],0)
    def test_execute(self):
        from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
        r=run_heartbeat_probe("execute")
        self.assertEqual(r["phase98_heartbeat_probe"]["healthy"],4)
        self.assertEqual(r["phase98_heartbeat_probe"]["blocked"],3)
    def test_skip_network(self):
        from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
        r=run_heartbeat_probe("skip-network")
        self.assertGreater(r["phase98_heartbeat_probe"]["warning"],0)

class TestPhase98RefreshFailure(unittest.TestCase):
    def test_failure(self):
        from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
        from smr_phase98_refresh_failure_detector import detect_refresh_failure
        hb=run_heartbeat_probe("execute")
        r=detect_refresh_failure(hb)
        self.assertGreaterEqual(r["phase98_refresh_failure_detector"]["failed_sources"],3)

class TestPhase98SchemaDrift(unittest.TestCase):
    def test_drift(self):
        from smr_phase98_schema_drift_detector import detect_schema_drift
        r=detect_schema_drift()
        self.assertEqual(r["phase98_schema_drift_detector"]["sources_checked"],7)
        self.assertEqual(r["phase98_schema_drift_detector"]["drift_sources"],0)

class TestPhase98FieldAvailability(unittest.TestCase):
    def test_avail(self):
        from smr_phase98_field_availability_monitor import monitor_field_availability
        r=monitor_field_availability()
        self.assertEqual(r["phase98_field_availability"]["sources_checked"],7)
        self.assertEqual(r["phase98_field_availability"]["field_regressions"],3)

class TestPhase98Staleness(unittest.TestCase):
    def test_stale(self):
        from smr_phase98_source_staleness_monitor import monitor_source_staleness
        r=monitor_source_staleness()
        self.assertEqual(r["phase98_source_staleness"]["total_sources"],7)
        self.assertGreaterEqual(r["phase98_source_staleness"]["expired"],3)

class TestPhase98ReliabilityDecay(unittest.TestCase):
    def test_decay(self):
        from smr_phase98_source_reliability_decay import compute_reliability_decay
        r=compute_reliability_decay()
        self.assertEqual(r["phase98_reliability_decay"]["total_sources"],7)
        self.assertEqual(r["phase98_reliability_decay"]["decay_sources"],3)

class TestPhase98BlockedEscalation(unittest.TestCase):
    def test_escalation(self):
        from smr_phase98_blocked_source_escalation import escalate_blocked_sources
        r=escalate_blocked_sources()
        self.assertEqual(r["phase98_blocked_escalation"]["total_blocked"],3)
        self.assertEqual(r["phase98_blocked_escalation"]["escalation_required"],1)

class TestPhase98AlertClassifier(unittest.TestCase):
    def test_classify(self):
        from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
        from smr_phase98_refresh_failure_detector import detect_refresh_failure
        from smr_phase98_schema_drift_detector import detect_schema_drift
        from smr_phase98_field_availability_monitor import monitor_field_availability
        from smr_phase98_source_staleness_monitor import monitor_source_staleness
        from smr_phase98_source_reliability_decay import compute_reliability_decay
        from smr_phase98_blocked_source_escalation import escalate_blocked_sources
        from smr_phase98_alert_classifier import classify_alerts
        hb=run_heartbeat_probe("execute");rf=detect_refresh_failure(hb);sd=detect_schema_drift()
        fa=monitor_field_availability();st=monitor_source_staleness();rd=compute_reliability_decay()
        be=escalate_blocked_sources();r=classify_alerts(hb,rf,sd,fa,st,rd,be)
        self.assertGreater(r["phase98_alert_classifier"]["alerts_created"],0)
        self.assertGreater(r["phase98_alert_classifier"]["severity_breakdown"]["warning"],0)

class TestPhase98AlertRouting(unittest.TestCase):
    def test_route(self):
        from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
        from smr_phase98_refresh_failure_detector import detect_refresh_failure
        from smr_phase98_schema_drift_detector import detect_schema_drift
        from smr_phase98_field_availability_monitor import monitor_field_availability
        from smr_phase98_source_staleness_monitor import monitor_source_staleness
        from smr_phase98_source_reliability_decay import compute_reliability_decay
        from smr_phase98_blocked_source_escalation import escalate_blocked_sources
        from smr_phase98_alert_classifier import classify_alerts
        from smr_phase98_alert_routing import route_alerts
        hb=run_heartbeat_probe("execute");rf=detect_refresh_failure(hb);sd=detect_schema_drift()
        fa=monitor_field_availability();st=monitor_source_staleness();rd=compute_reliability_decay()
        be=escalate_blocked_sources();al=classify_alerts(hb,rf,sd,fa,st,rd,be);r=route_alerts(al)
        self.assertTrue(r["phase98_alert_routing"]["external_disabled"])

class TestPhase98AlertHistory(unittest.TestCase):
    def test_dry(self):
        from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
        from smr_phase98_refresh_failure_detector import detect_refresh_failure
        from smr_phase98_schema_drift_detector import detect_schema_drift
        from smr_phase98_field_availability_monitor import monitor_field_availability
        from smr_phase98_source_staleness_monitor import monitor_source_staleness
        from smr_phase98_source_reliability_decay import compute_reliability_decay
        from smr_phase98_blocked_source_escalation import escalate_blocked_sources
        from smr_phase98_alert_classifier import classify_alerts
        from smr_phase98_alert_history import write_alert_history
        hb=run_heartbeat_probe("execute");rf=detect_refresh_failure(hb);sd=detect_schema_drift()
        fa=monitor_field_availability();st=monitor_source_staleness();rd=compute_reliability_decay()
        be=escalate_blocked_sources();al=classify_alerts(hb,rf,sd,fa,st,rd,be)
        r=write_alert_history(al,"dry-run")
        self.assertEqual(r["phase98_alert_history"]["mode"],"dry-run")
        self.assertTrue(r["phase98_alert_history"]["alert_history_path_ignored"])
    def test_execute(self):
        from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
        from smr_phase98_refresh_failure_detector import detect_refresh_failure
        from smr_phase98_schema_drift_detector import detect_schema_drift
        from smr_phase98_field_availability_monitor import monitor_field_availability
        from smr_phase98_source_staleness_monitor import monitor_source_staleness
        from smr_phase98_source_reliability_decay import compute_reliability_decay
        from smr_phase98_blocked_source_escalation import escalate_blocked_sources
        from smr_phase98_alert_classifier import classify_alerts
        from smr_phase98_alert_history import write_alert_history, read_alert_history
        hb=run_heartbeat_probe("execute");rf=detect_refresh_failure(hb);sd=detect_schema_drift()
        fa=monitor_field_availability();st=monitor_source_staleness();rd=compute_reliability_decay()
        be=escalate_blocked_sources();al=classify_alerts(hb,rf,sd,fa,st,rd,be)
        w=write_alert_history(al,"execute")
        self.assertGreater(w["phase98_alert_history"]["alerts_written"],0)
        h=read_alert_history()
        self.assertGreater(h["phase98_alert_history_read"]["alerts_loaded"],0)

class TestPhase98IncidentReport(unittest.TestCase):
    def test_incident(self):
        from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
        from smr_phase98_refresh_failure_detector import detect_refresh_failure
        from smr_phase98_source_staleness_monitor import monitor_source_staleness
        from smr_phase98_blocked_source_escalation import escalate_blocked_sources
        from smr_phase98_source_incident_report import build_incident_report
        hb=run_heartbeat_probe("execute");rf=detect_refresh_failure(hb);st=monitor_source_staleness()
        be=escalate_blocked_sources();r=build_incident_report(hb,rf,st,be)
        self.assertGreater(r["phase98_source_incident_report"]["total_incidents"],0)

class TestPhase98HealthBoard(unittest.TestCase):
    def test_board(self):
        from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
        from smr_phase98_source_staleness_monitor import monitor_source_staleness
        from smr_phase98_source_reliability_decay import compute_reliability_decay
        from smr_phase98_daily_source_health_board import build_health_board
        hb=run_heartbeat_probe("execute");st=monitor_source_staleness();rd=compute_reliability_decay()
        r=build_health_board(hb,st,rd)
        self.assertEqual(r["phase98_health_board"]["sources"],7)
        self.assertGreaterEqual(r["phase98_health_board"]["warning"],3)

class TestPhase98HealthMatrix(unittest.TestCase):
    def test_matrix(self):
        from smr_phase98_ticker_domain_source_health_matrix import build_health_matrix
        r=build_health_matrix()
        self.assertEqual(len(r["phase98_health_matrix"]["tickers"]),8)
        self.assertEqual(len(r["phase98_health_matrix"]["domains"]),6)
        self.assertEqual(len(r["phase98_health_matrix"]["sources"]),7)

class TestPhase98IntegrationCheck(unittest.TestCase):
    def test_integration(self):
        from smr_phase98_phase97_integration_check import check_phase97_integration
        r=check_phase97_integration()
        self.assertEqual(r["phase98_phase97_integration_check"]["overall"],"pass")

class TestPhase98QualityGate(unittest.TestCase):
    def test_gate(self):
        from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
        from smr_phase98_schema_drift_detector import detect_schema_drift
        from smr_phase98_field_availability_monitor import monitor_field_availability
        from smr_phase98_source_staleness_monitor import monitor_source_staleness
        from smr_phase98_monitoring_quality_gate import run_monitoring_quality_gate
        hb=run_heartbeat_probe("execute");sd=detect_schema_drift();fa=monitor_field_availability()
        st=monitor_source_staleness();r=run_monitoring_quality_gate(hb,sd,fa,st)
        self.assertEqual(r["phase98_monitoring_quality_gate"]["overall"],"pass")

class TestPhase98Guard(unittest.TestCase):
    def test_guard(self):
        from smr_phase98_endpoint_heartbeat import run_heartbeat_probe
        from smr_phase98_refresh_failure_detector import detect_refresh_failure
        from smr_phase98_schema_drift_detector import detect_schema_drift
        from smr_phase98_field_availability_monitor import monitor_field_availability
        from smr_phase98_source_staleness_monitor import monitor_source_staleness
        from smr_phase98_source_reliability_decay import compute_reliability_decay
        from smr_phase98_blocked_source_escalation import escalate_blocked_sources
        from smr_phase98_alert_classifier import classify_alerts
        from smr_phase98_monitoring_cannot_conclude_guard import run_monitoring_guard
        hb=run_heartbeat_probe("execute");rf=detect_refresh_failure(hb);sd=detect_schema_drift()
        fa=monitor_field_availability();st=monitor_source_staleness();rd=compute_reliability_decay()
        be=escalate_blocked_sources();al=classify_alerts(hb,rf,sd,fa,st,rd,be);r=run_monitoring_guard(al)
        self.assertEqual(r["phase98_monitoring_guard"]["overall"],"pass")

class TestPhase98Backlog(unittest.TestCase):
    def test_backlog(self):
        from smr_phase98_backlog_update import build_backlog_update
        r=build_backlog_update()
        self.assertEqual(r["phase98_backlog_update"]["items"],10)
    def test_phase99(self):
        from smr_phase98_backlog_update import build_backlog_update
        self.assertIn("phase99_recommendation",build_backlog_update()["phase98_backlog_update"])

class TestPhase98Runner(unittest.TestCase):
    def test_dry(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase98_live_source_monitoring_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--dry-run","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase98_pipeline"]
            self.assertEqual(d["mode"],"dry-run")
            self.assertGreater(d["sources_monitored"],0)
        finally:sys.argv=o
    def test_exec(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase98_live_source_monitoring_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase98_pipeline"]
            self.assertEqual(d["mode"],"execute")
            self.assertGreater(d["alerts_created"],0)
        finally:sys.argv=o
    def test_skip_network(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase98_live_source_monitoring_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--skip-network","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            d=json.loads(buf.getvalue())["phase98_pipeline"]
            self.assertEqual(d["mode"],"skip-network")
        finally:sys.argv=o
    def test_no_pending(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
        from run_phase98_live_source_monitoring_pipeline import main as rm
        o=sys.argv[:]
        try:
            sys.argv=["r.py","--execute","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):rm()
            p=json.loads(buf.getvalue())["phase98_pipeline"]
            self.assertEqual(p["pending_created"],0)
            self.assertFalse(p["mock_used"])
        finally:sys.argv=o

class TestPhase98Dashboard(unittest.TestCase):
    def test_dash(self):
        sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
        from build_phase98_dashboard import main as dm
        o=sys.argv[:]
        try:
            sys.argv=["d.py","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):dm()
            d=json.loads(buf.getvalue())["summary"]
            self.assertEqual(d["phase"],"phase98")
            self.assertFalse(d["mock_used"])
            self.assertEqual(d["pending_created"],0)
            self.assertFalse(d["external_notification_enabled"])
        finally:sys.argv=o

if __name__=="__main__":
    unittest.main()

