#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_real_business_source_coverage_audit import audit_coverage

class TestRealCoverageAudit(unittest.TestCase):
    def test_returns_valid_structure(self):
        r = audit_coverage('300308.SZ')
        self.assertIn('real_business_source_coverage_audit', r)
        d = r['real_business_source_coverage_audit']
        self.assertEqual(d['business_variables'], 7)
        self.assertIn('coverage_status', d)

    def test_all_variables_covered(self):
        r = audit_coverage('300308.SZ')
        d = r['real_business_source_coverage_audit']
        self.assertEqual(d['variables_with_real_text_coverage'], 7)
        self.assertEqual(d['variables_without_real_text_coverage'], 0)

    def test_coverage_rows_complete(self):
        r = audit_coverage('300308.SZ')
        rows = r['real_business_source_coverage_audit']['coverage_rows']
        self.assertEqual(len(rows), 7)
        for row in rows:
            self.assertIn('coverage_status', row)
            self.assertIn('real_text_sources', row)

    def test_coverage_not_evidence(self):
        r = audit_coverage('300308.SZ')
        rows = r['real_business_source_coverage_audit']['coverage_rows']
        for row in rows:
            self.assertNotIn('confirmed', row.get('coverage_status', ''))

if __name__ == '__main__': unittest.main()
