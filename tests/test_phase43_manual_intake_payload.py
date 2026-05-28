import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase43_manual_intake_samples import build_payload


class Phase43ManualIntakePayloadTests(unittest.TestCase):
    def test_three_sample_payloads_are_available_without_writes(self):
        payload = build_payload("300308.SZ")
        body = payload["manual_intake_samples"]
        self.assertEqual(body["sample_count"], 3)
        self.assertEqual({row["evidence_type"] for row in body["samples"]}, {"official_consensus", "supplier_share", "confirmed_customer_allocation"})
        self.assertTrue(all(row["raw_file_attached"] is False for row in body["samples"]))
        self.assertTrue(all(row["limitations"] for row in body["samples"]))
        self.assertEqual(body["pending_created"], 0)
        self.assertFalse(payload["safety"]["evidence_written"])


if __name__ == "__main__":
    unittest.main()
