import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase42_customer_allocation_proxy_audit import build_payload
from phase42_helpers import make_phase42_conn


class Phase42CustomerAllocationProxyAuditTests(unittest.TestCase):
    def test_customer_allocation_proxy_audit_has_zero_confirmed_and_violations(self):
        payload = build_payload(make_phase42_conn(), "300308.SZ")
        body = payload["customer_allocation_proxy_audit"]
        self.assertEqual(body["confirmed_allocation_items"], 0)
        self.assertEqual(body["violations"], 0)
        self.assertEqual(body["proxy_items_checked"], 3)
        self.assertTrue(all(row["status"] == "proxy_only" for row in body["audit_rows"]))


if __name__ == "__main__":
    unittest.main()
