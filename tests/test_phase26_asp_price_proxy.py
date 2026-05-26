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

from build_phase26_asp_price_proxy import build_payload


class Phase26AspPriceProxyTests(unittest.TestCase):
    def test_asp_pack_does_not_fabricate_asp(self):
        payload = build_payload(sqlite3.connect(":memory:"), ticker="300394.SZ")
        pack = payload["asp_price_proxy"]
        self.assertFalse(pack["direct_ASP_disclosed"])
        self.assertFalse(pack["industry_price_proxy_available"])
        self.assertEqual(pack["allowed_usage"], "scenario_analysis_only")
        self.assertIsNone(pack["assumption_range"]["base"])
        self.assertIn("product ASP", pack["missing_variables"])


if __name__ == "__main__":
    unittest.main()
