import unittest, json, sys, os, tempfile
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestEvidenceMemoryWriter(unittest.TestCase):
    def setUp(self):
        from smr_evidence_memory_writer import MEMORY_DIR
        self.mem_dir = MEMORY_DIR

    def test_write_dry_run(self):
        from smr_evidence_memory_writer import write_evidence_memory
        ev = [{'evidence_id': 'ev_001', 'business_variable': '800G_product_signal',
               'source_id': 's1', 'source_type': 'annual_report', 'title': 'test',
               'evidence_strength': 'financial_report_context', 'confidence': 'low',
               'claim_type': 'supported', 'limitation': 'test', 'cannot_conclude': ['x'],
               'requires_human_review': False}]
        r = write_evidence_memory('300308.SZ', ev, dry_run=True)
        self.assertEqual(r['input_deep_evidence'], 1)
        self.assertEqual(r['records_written'], 1)
        self.assertTrue(r['memory_path_ignored'])

    def test_write_execute(self):
        from smr_evidence_memory_writer import write_evidence_memory
        ev = [{'evidence_id': 'ev_t1', 'business_variable': '800G_product_signal',
               'source_id': 's1', 'source_type': 'annual_report', 'title': 'T',
               'evidence_strength': 'business_context', 'confidence': 'low',
               'claim_type': 's', 'limitation': '', 'cannot_conclude': [],
               'requires_human_review': False}]
        r = write_evidence_memory('300308.SZ', ev, dry_run=False)
        self.assertEqual(r['records_written'], 1)
        # Check file was written
        fpath = self.mem_dir / 'evidence_memory_300308_SZ.json'
        self.assertTrue(fpath.exists())

    def test_dedupe(self):
        from smr_evidence_memory_writer import write_evidence_memory
        ev = [
            {'evidence_id': 'dup_1', 'business_variable': 'v1', 'source_id': 's1',
             'source_type': 't', 'title': 't', 'evidence_strength': 'business_context',
             'confidence': 'low', 'claim_type': 's', 'limitation': '', 'cannot_conclude': [],
             'requires_human_review': False},
            {'evidence_id': 'dup_1', 'business_variable': 'v2', 'source_id': 's2',
             'source_type': 't', 'title': 't', 'evidence_strength': 'business_context',
             'confidence': 'low', 'claim_type': 's', 'limitation': '', 'cannot_conclude': [],
             'requires_human_review': False},
        ]
        r = write_evidence_memory('300308.SZ', ev, dry_run=True)
        self.assertEqual(r['records_written'], 1)
        self.assertEqual(r['duplicate_records'], 1)

if __name__ == '__main__': unittest.main()
