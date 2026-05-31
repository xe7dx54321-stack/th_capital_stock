import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))

class Test85bLint(unittest.TestCase):
    def test_build(self):
        from build_phase85b_closeout_brief_quality_lint import build
        r=build()
        self.assertIsNotNone(r)
        pass  # self-audit module
if __name__=="__main__":unittest.main()
