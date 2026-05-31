import unittest, sys, os, json
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","reporting"))
from build_phase91_reality_audit_dashboard import main as dash_main
import io, contextlib

class TestDashboard(unittest.TestCase):
    def test_dashboard_json(self):
        old_argv=sys.argv[:]
        try:
            sys.argv=["dash.py","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):
                dash_main()
            output=buf.getvalue()
            d=json.loads(output)
            s=d["summary"]
            self.assertEqual(s["tickers_audited"],8)
            self.assertEqual(s["audit_status"],"complete")
        finally:
            sys.argv=old_argv
    def test_no_mock(self):
        old_argv=sys.argv[:]
        try:
            sys.argv=["dash.py","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):
                dash_main()
            output=buf.getvalue()
            d=json.loads(output)
            self.assertFalse(d["summary"]["mock_used"])
            self.assertFalse(d["summary"]["fixture_used"])
        finally:
            sys.argv=old_argv
    def test_no_pending(self):
        old_argv=sys.argv[:]
        try:
            sys.argv=["dash.py","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):
                dash_main()
            output=buf.getvalue()
            d=json.loads(output)
            self.assertEqual(d["summary"]["pending_created"],0)
            self.assertEqual(d["summary"]["real_trade_created"],0)
        finally:
            sys.argv=old_argv
    def test_blocked_count(self):
        old_argv=sys.argv[:]
        try:
            sys.argv=["dash.py","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):
                dash_main()
            output=buf.getvalue()
            d=json.loads(output)
            self.assertEqual(d["summary"]["blocked_source"],1)
        finally:
            sys.argv=old_argv
    def test_curated_catalogs_not_zero(self):
        old_argv=sys.argv[:]
        try:
            sys.argv=["dash.py","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):
                dash_main()
            output=buf.getvalue()
            d=json.loads(output)
            self.assertGreater(d["summary"]["curated_catalog_source"],0)
        finally:
            sys.argv=old_argv
