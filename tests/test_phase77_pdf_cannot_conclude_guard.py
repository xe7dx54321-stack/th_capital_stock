import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestCannotConcludeGuard(unittest.TestCase):
    def test_guard_pass(self):
        from build_phase77_pdf_cannot_conclude_guard import build
        r=build();g=r["phase77_pdf_cannot_conclude_guard"]
        self.assertEqual(g["guard_status"],"pass")
        self.assertEqual(g["violations"],0)
    def test_no_pending(self):
        from build_phase77_pdf_cannot_conclude_guard import build
        r=build();g=r["phase77_pdf_cannot_conclude_guard"]
        self.assertEqual(g["pending_created"],0)
if __name__=="__main__":unittest.main()
