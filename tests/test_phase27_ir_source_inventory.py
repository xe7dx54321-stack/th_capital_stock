import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase27_ir_source_inventory import build_payload
from smr_ir_source_inventory import build_ir_source_inventory


class Phase27IRSourceInventoryTests(unittest.TestCase):
    def test_inventory_for_pilot_tickers(self):
        payload = build_payload(tickers="300394.SZ,300308.SZ,688041.SH,002230.SZ")
        self.assertEqual(payload["summary"]["tickers_checked"], 4)
        self.assertGreaterEqual(payload["summary"]["sources_found"], 4)
        single = build_ir_source_inventory("300394.SZ")
        self.assertIn("investor_relations_record", single["source_inventory"]["sources_by_type"])


if __name__ == "__main__":
    unittest.main()
