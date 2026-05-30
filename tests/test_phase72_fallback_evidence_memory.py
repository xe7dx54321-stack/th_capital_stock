import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestEvidenceMemory(unittest.TestCase):
    def test_has_rows(self):
        from build_phase72_fallback_evidence_memory_report import build
        r = build(); d = r["phase72_fallback_evidence_memory_report"]
        self.assertGreaterEqual(len(d["rows"]), 2)
    def test_memory_ignored(self):
        from build_phase72_fallback_evidence_memory_report import build
        r = build(); d = r["phase72_fallback_evidence_memory_report"]
        self.assertTrue(d.get("memory_path_ignored", False))
    def test_no_fake_write(self):
        from build_phase72_fallback_evidence_memory_report import build
        r = build(); d = r["phase72_fallback_evidence_memory_report"]
        for row in d["rows"]:
            if row["records_written"] == 0:
                self.assertIn("reason", row)
if __name__ == "__main__": unittest.main()
