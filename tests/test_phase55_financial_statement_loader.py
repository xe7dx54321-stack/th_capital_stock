import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
class Phase55LoaderTests(unittest.TestCase):
    def test_dry_run_does_not_write(self):
        from smr_financial_statement_loader import load_financial_statements
        r = load_financial_statements(mode='dry-run')
        ld = r['financial_statement_loader']
        self.assertEqual(ld['records_written'], 0)
    def test_fixture_is_marked(self):
        from smr_financial_statement_loader import load_financial_statements
        r = load_financial_statements()
        ld = r['financial_statement_loader']
        self.assertTrue(ld['fixture_used'])
    def test_records_have_required_fields(self):
        from smr_financial_statement_loader import load_financial_statements
        r = load_financial_statements()
        ld = r['financial_statement_loader']
        recs = ld['records']
        self.assertGreater(len(recs), 0)
        for rec in recs:
            self.assertIn('period', rec)
            self.assertIn('metric', rec)
            self.assertIn('value', rec)

if __name__ == '__main__':
    unittest.main()
