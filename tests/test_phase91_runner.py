import unittest, sys, os, json
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","lib"))
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","08_scripts","jobs"))
from run_phase91_information_source_reality_audit_pipeline import main as run_main
import io, contextlib

class TestRunner(unittest.TestCase):
    def test_import_ok(self):
        self.assertTrue(True)
    def test_dry_run_no_error(self):
        old_argv=sys.argv[:]
        try:
            sys.argv=["runner.py","--dry-run","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):
                run_main()
            output=buf.getvalue()
            d=json.loads(output)
            p=d["phase91_information_source_reality_audit_pipeline"]
            self.assertEqual(p["mode"],"dry-run")
        finally:
            sys.argv=old_argv
    def test_execute_no_error(self):
        old_argv=sys.argv[:]
        try:
            sys.argv=["runner.py","--execute","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):
                run_main()
            output=buf.getvalue()
            d=json.loads(output)
            p=d["phase91_information_source_reality_audit_pipeline"]
            self.assertEqual(p["mode"],"execute")
            self.assertEqual(p["tickers_audited"],8)
        finally:
            sys.argv=old_argv
    def test_skip_network_no_error(self):
        old_argv=sys.argv[:]
        try:
            sys.argv=["runner.py","--skip-network","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):
                run_main()
            output=buf.getvalue()
            d=json.loads(output)
            p=d["phase91_information_source_reality_audit_pipeline"]
            self.assertEqual(p["mode"],"skip-network")
        finally:
            sys.argv=old_argv
    def test_no_pending(self):
        old_argv=sys.argv[:]
        try:
            sys.argv=["runner.py","--execute","--json"]
            buf=io.StringIO()
            with contextlib.redirect_stdout(buf):
                run_main()
            output=buf.getvalue()
            d=json.loads(output)
            p=d["phase91_information_source_reality_audit_pipeline"]
            self.assertEqual(p["pending_created"],0)
            self.assertEqual(p["paper_order_created"],0)
            self.assertEqual(p["real_trade_created"],0)
            self.assertEqual(p["mock_used"],False)
        finally:
            sys.argv=old_argv
