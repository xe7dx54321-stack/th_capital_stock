#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parent.parent/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
class TestPhase65AnnouncementQueryMatrix(unittest.TestCase):
    def test_skip_network(self):
        from smr_cninfo_announcement_query_matrix import run_announcement_query_matrix
        r=run_announcement_query_matrix("300308.SZ",skip_network=True)
        m=r["cninfo_announcement_query_matrix"]
        self.assertFalse(m["network_attempted"])
        self.assertEqual(m["status"],"skipped_network_disabled")
    def test_successful_sets_zero_on_skip(self):
        from smr_cninfo_announcement_query_matrix import run_announcement_query_matrix
        r=run_announcement_query_matrix("300308.SZ",skip_network=True)
        m=r["cninfo_announcement_query_matrix"]
        self.assertEqual(m["successful_sets"],0)
    def test_no_mock_no_fixture(self):
        from smr_cninfo_announcement_query_matrix import run_announcement_query_matrix
        r=run_announcement_query_matrix("300308.SZ",skip_network=True)
        m=r["cninfo_announcement_query_matrix"]
        self.assertFalse(m["mock_used"])
        self.assertFalse(m["fixture_used"])
if __name__=="__main__":unittest.main()
