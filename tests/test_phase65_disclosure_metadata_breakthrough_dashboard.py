#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parent.parent/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
class TestPhase65Dashboard(unittest.TestCase):
    def test_dashboard_breakthrough_false_on_skip(self):
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"08_scripts"/"reporting"))
        from build_phase65_disclosure_metadata_breakthrough_dashboard import build
        r=build(skip=True)
        s=r.get("summary",r)
        self.assertFalse(s["metadata_breakthrough"])
        self.assertEqual(s["business_evidence_delta"],0)
    def test_no_mock_fixture_raw_ocr(self):
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"08_scripts"/"reporting"))
        from build_phase65_disclosure_metadata_breakthrough_dashboard import build
        r=build(skip=True)
        s=r.get("summary",r)
        self.assertFalse(s["mock_used"])
        self.assertFalse(s["fixture_used"])
        self.assertFalse(s["raw_saved"])
        self.assertFalse(s["ocr_used"])
    def test_pending_order_trade_zero(self):
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"08_scripts"/"reporting"))
        from build_phase65_disclosure_metadata_breakthrough_dashboard import build
        r=build(skip=True)
        s=r.get("summary",r)
        self.assertEqual(s["pending_created"],0)
        self.assertEqual(s["paper_order_created"],0)
        self.assertEqual(s["real_trade_created"],0)
if __name__=="__main__":unittest.main()
