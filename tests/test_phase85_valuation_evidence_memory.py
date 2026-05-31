import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestEvidenceMemory(unittest.TestCase):
    def test_build(self):from build_phase85_valuation_evidence_memory_report import build;r=build();e=r["phase85_evidence_memory_report"];self.assertGreater(e["records_written_total"],0)
    def test_path_ignored(self):from build_phase85_valuation_evidence_memory_report import build;r=build();e=r["phase85_evidence_memory_report"];self.assertTrue(e["memory_path_ignored"])
if __name__=="__main__":unittest.main()
