import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestSourceTraceIndex(unittest.TestCase):
    def test_empty(self):
        from smr_evidence_source_trace_index import build_source_trace_index
        r = build_source_trace_index([])
        self.assertEqual(r['evidence_records_checked'], 0)

    def test_traceable(self):
        from smr_evidence_source_trace_index import build_source_trace_index
        ev = [{'evidence_id': 'e1', 'source_id': 's1', 'source_type': 't', 'source_title': 'T',
               'text_hash': 'abc', 'span_location_or_hash': 'xyz', 'quoted_span': 'text'}]
        r = build_source_trace_index(ev)
        self.assertEqual(r['high_traceability'], 1)
        self.assertEqual(r['trace_failed'], 0)
        self.assertEqual(r['trace_status'], 'pass')

    def test_failed(self):
        from smr_evidence_source_trace_index import build_source_trace_index
        ev = [{'evidence_id': 'e1'}]
        r = build_source_trace_index(ev)
        self.assertEqual(r['trace_failed'], 1)

if __name__ == '__main__': unittest.main()
