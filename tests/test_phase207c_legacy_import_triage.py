import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_scripts", "lib"))

from smr_phase207c_test_suite_health import build_legacy_import_debt_report


class Phase207cLegacyImportTriageTest(unittest.TestCase):
    def test_paper_portfolio_import_debt_fixed(self):
        report = build_legacy_import_debt_report(write=False)["phase207c_legacy_import_debt_report"]
        self.assertEqual(report["test_file"], "tests/test_paper_portfolio.py")
        self.assertFalse(report["import_error_detected"])
        self.assertTrue(report["safe_fix_available"])
        self.assertTrue(report["fix_applied"])
        self.assertFalse(report["quarantine_required"])
        self.assertFalse(report["silent_skip_used"])
        self.assertFalse(report["production_semantics_changed"])


if __name__ == "__main__":
    unittest.main()
