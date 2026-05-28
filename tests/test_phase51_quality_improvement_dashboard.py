import unittest, json; from build_phase51_quality_improvement_dashboard import main as dash_main
import sys; from io import StringIO
class Phase51DashboardTests(unittest.TestCase):
    def test_json_output(self):
        old_argv = sys.argv[:]; old_stdout = sys.stdout
        try:
            sys.argv = ["build_phase51_quality_improvement_dashboard.py", "--json"]
            sys.stdout = StringIO()
            dash_main()
            output = sys.stdout.getvalue()
            d = json.loads(output)
            self.assertIn("summary", d)
            self.assertEqual(d["summary"]["pending_created"], 0)
            self.assertEqual(d["summary"]["paper_order_created"], 0)
        finally:
            sys.argv = old_argv; sys.stdout = old_stdout
    def test_no_pending(self):
        old_argv = sys.argv[:]; old_stdout = sys.stdout
        try:
            sys.argv = ["build_phase51_quality_improvement_dashboard.py", "--json"]
            sys.stdout = StringIO()
            dash_main()
            d = json.loads(sys.stdout.getvalue())
            self.assertEqual(d["summary"]["pending_created"], 0)
        finally:
            sys.argv = old_argv; sys.stdout = old_stdout
if __name__ == "__main__": unittest.main()
