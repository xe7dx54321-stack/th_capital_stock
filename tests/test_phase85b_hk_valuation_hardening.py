import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))

class Test85bHK(unittest.TestCase):
    def test_build(self):
        from build_phase85b_hk_valuation_hardening_report import build
        r=build()
        self.assertIsNotNone(r)
        k=r.get("phase85b_hk_valuation_hardening",r)
        if isinstance(k,dict):
            self.assertFalse(k.get("mock_used",True))
            self.assertFalse(k.get("fixture_used",True))
if __name__=="__main__":unittest.main()
