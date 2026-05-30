import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestClassifier(unittest.TestCase):
    def test_build(self):from build_phase84_daily_status_classifier_report import build;r=build();c=r["phase84_daily_status_classifier"];self.assertGreater(c["tickers_classified"],0)
    def test_blocked_priority(self):from build_phase84_daily_status_classifier_report import build;r=build();rows=r["phase84_daily_status_classifier"]["rows"];b=[r for r in rows if r["blocked"]];self.assertEqual(len(b),1)
    def test_sections(self):from build_phase84_daily_status_classifier_report import build;r=build();c=r["phase84_daily_status_classifier"];self.assertIn("strengthened",c);self.assertIn("weakened",c);self.assertIn("unchanged",c)
if __name__=="__main__":unittest.main()
