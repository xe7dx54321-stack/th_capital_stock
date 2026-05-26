import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase26_customer_allocation_proxy import build_payload


class Phase26CustomerAllocationProxyTests(unittest.TestCase):
    def test_customer_allocation_is_not_fabricated(self):
        payload = build_payload(sqlite3.connect(":memory:"), ticker="300394.SZ")
        pack = payload["customer_allocation_proxy"]
        self.assertFalse(pack["confirmed_customer_allocation"])
        self.assertEqual(pack["evidence_status"], "missing")
        self.assertEqual(pack["evidence_ids"], [])
        self.assertIn("no direct NVIDIA/hyperscaler supply evidence", pack["limitations"])


if __name__ == "__main__":
    unittest.main()
