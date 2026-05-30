import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestAvailIntegration(unittest.TestCase):
    def test_build(self):from build_phase83_hk_us_structured_availability_integration import build;r=build();ai=r["phase83_hk_us_structured_availability_integration"];self.assertGreater(ai["phase83_hk_us_new_available"],0)
    def test_after_gt_before(self):from build_phase83_hk_us_structured_availability_integration import build;r=build();ai=r["phase83_hk_us_structured_availability_integration"];self.assertGreaterEqual(ai["structured_available_after_phase83"],ai["phase82_structured_available"])
if __name__=="__main__":unittest.main()
