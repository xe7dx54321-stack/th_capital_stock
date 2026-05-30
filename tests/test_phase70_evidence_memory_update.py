import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestEvidenceMemoryUpdate(unittest.TestCase):
    def test_has_rows(self):
        from build_phase70_evidence_memory_update_report import build
        r = build(); d = r["phase70_evidence_memory_update"]
        self.assertEqual(len(d["rows"]), 3)
    def test_memory_path_ignored(self):
        from build_phase70_evidence_memory_update_report import build
        r = build(); d = r["phase70_evidence_memory_update"]
        self.assertTrue(d.get("memory_path_ignored", False))
    def test_no_fake_write(self):
        from build_phase70_evidence_memory_update_report import build
        r = build(); d = r["phase70_evidence_memory_update"]
        for row in d["rows"]:
            if row["records_written"] == 0:
                self.assertIn("reason", row)
    def test_no_mock_fixture(self):
        from build_phase70_evidence_memory_update_report import build
        r = build(); d = r["phase70_evidence_memory_update"]
        self.assertFalse(d.get("mock_used",True)); self.assertFalse(d.get("fixture_used",True))
if __name__ == "__main__": unittest.main()
