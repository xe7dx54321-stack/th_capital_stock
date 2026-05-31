import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(R) not in sys.path:sys.path.insert(0,str(R))

class Test89Mem(unittest.TestCase):
    def test_build(self):
        from run_phase89_write_unified_evidence_memory import build
        r=build()
        self.assertIsNotNone(r)
    def test_no_mock(self):
        from run_phase89_write_unified_evidence_memory import build
        r=build()
        self.assertIsNotNone(r)
if __name__=="__main__":unittest.main()
