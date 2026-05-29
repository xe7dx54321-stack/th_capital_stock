import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
J = Path(__file__).resolve().parents[1] / '08_scripts' / 'jobs'
R = Path(__file__).resolve().parents[1] / '08_scripts' / 'reporting'
for p in [str(L), str(J), str(R)]:
    if p not in sys.path: sys.path.insert(0, p)

class TestEvidenceMemoryUpdate(unittest.TestCase):
    def test_dry_run_has_rows(self):
        from run_phase69b_write_real_execute_evidence_memory import run
        r = run(dry_run=True)
        mem = r['phase69b_evidence_memory_write']
        self.assertIn('rows', mem)
        self.assertEqual(len(mem['rows']), 3)

    def test_execute_has_300308_records(self):
        from run_phase69b_write_real_execute_evidence_memory import run
        r = run(dry_run=False)
        mem = r['phase69b_evidence_memory_write']
        row308 = [row for row in mem['rows'] if row['ticker'] == '300308.SZ']
        self.assertTrue(len(row308) > 0)
        self.assertGreaterEqual(row308[0]['records_written'], 1)

    def test_no_fake_write_on_no_evidence(self):
        from run_phase69b_write_real_execute_evidence_memory import run
        r = run(dry_run=False)
        mem = r['phase69b_evidence_memory_write']
        for row in mem['rows']:
            if row['records_written'] == 0:
                self.assertIn('reason', row)

    def test_memory_path_ignored(self):
        from run_phase69b_write_real_execute_evidence_memory import run
        r = run(dry_run=False)
        mem = r['phase69b_evidence_memory_write']
        self.assertTrue(mem.get('memory_path_ignored', False))

    def test_no_mock_fixture(self):
        from run_phase69b_write_real_execute_evidence_memory import run
        r = run(dry_run=False)
        mem = r['phase69b_evidence_memory_write']
        self.assertFalse(mem.get('mock_used', True))
        self.assertFalse(mem.get('fixture_used', True))

    def test_report_outputs(self):
        from build_phase69b_evidence_memory_update_report import build
        r = build()
        self.assertIsNotNone(r)

if __name__ == '__main__': unittest.main()
