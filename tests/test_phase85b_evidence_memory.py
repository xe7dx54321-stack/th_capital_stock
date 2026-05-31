import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(R) not in sys.path:sys.path.insert(0,str(R))

class Test85bMemory(unittest.TestCase):
    def test_build(self):
        from run_phase85b_write_valuation_hardening_evidence_memory import build
        r=build()
        self.assertIsNotNone(r)
        pass  # self-audit module
if __name__=="__main__":unittest.main()
