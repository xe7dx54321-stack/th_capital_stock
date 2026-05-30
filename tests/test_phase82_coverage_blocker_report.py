import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestBlockerReport(unittest.TestCase):
    def test_build(self):from build_phase82_coverage_blocker_report import build;r=build();b=r["phase82_coverage_blocker_report"];self.assertGreater(b["blocked_tickers"],0)
    def test_has_next_action(self):from build_phase82_coverage_blocker_report import build;r=build();rows=r["phase82_coverage_blocker_report"]["rows"];self.assertTrue(all(len(row["allowed_next_action"])>0 for row in rows))
    def test_specific_blockers(self):from build_phase82_coverage_blocker_report import build;r=build();rows=r["phase82_coverage_blocker_report"]["rows"];self.assertTrue(all(len(row["most_specific_blocker"])>0 for row in rows))
if __name__=="__main__":unittest.main()
