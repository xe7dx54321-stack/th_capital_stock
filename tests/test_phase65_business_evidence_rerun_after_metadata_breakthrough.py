#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parent.parent/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
class TestPhase65BusinessEvidenceRerun(unittest.TestCase):
    def test_skip_network_delta_zero(self):
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"08_scripts"/"reporting"))
        from build_phase65_business_evidence_rerun_after_metadata_breakthrough import build
        r=build("300308.SZ",skip=True)
        b=r["business_evidence_rerun_after_metadata_breakthrough"]
        self.assertFalse(b["metadata_breakthrough"])
        self.assertEqual(b["evidence_gain_delta"],0)
        self.assertEqual(b["status"],"skipped_no_real_text_available")
    def test_no_mock_no_fixture(self):
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"08_scripts"/"reporting"))
        from build_phase65_business_evidence_rerun_after_metadata_breakthrough import build
        r=build("300308.SZ",skip=True)
        b=r["business_evidence_rerun_after_metadata_breakthrough"]
        self.assertFalse(b["mock_used"])
        self.assertFalse(b["fixture_used"])
    def test_guard_pass(self):
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"08_scripts"/"reporting"))
        from build_phase65_business_evidence_rerun_after_metadata_breakthrough import build
        r=build("300308.SZ",skip=True)
        b=r["business_evidence_rerun_after_metadata_breakthrough"]
        self.assertEqual(b["guard_status"],"pass")
if __name__=="__main__":unittest.main()
