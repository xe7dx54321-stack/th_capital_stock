import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestBlockerReport(unittest.TestCase):
    def test_build(self):from build_phase83_hk_us_coverage_blocker_report import build;r=build();b=r["phase83_hk_us_coverage_blocker_report"];self.assertGreaterEqual(b["blocked_tickers"],0)
    def test_has_next_action(self):from build_phase83_hk_us_coverage_blocker_report import build;r=build();rows=r["phase83_hk_us_coverage_blocker_report"]["rows"];self.assertTrue(all(len(row.get("allowed_next_action",""))>0 for row in rows) if rows else True)
    def test_specific_blockers(self):from build_phase83_hk_us_coverage_blocker_report import build;r=build();rows=r["phase83_hk_us_coverage_blocker_report"]["rows"];self.assertTrue(all(len(row.get("most_specific_blocker",""))>0 for row in rows) if rows else True)
if __name__=="__main__":unittest.main()
