import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_valuation import build_peer_set_snapshot, peer_set_definition, valuation_sub_blockers


class Phase10PeerSetTests(unittest.TestCase):
    def test_09988_peer_set_loads(self):
        peer_set_id, peer_set = peer_set_definition("09988.HK")

        self.assertEqual(peer_set_id, "hk_internet_platforms")
        self.assertIn("00700.HK", peer_set["tickers"])

    def test_peer_data_missing_is_specific(self):
        conn = sqlite3.connect(":memory:")
        snapshot = build_peer_set_snapshot(conn, "09988.HK", {})
        blockers = valuation_sub_blockers(
            {
                "missing_data": ["peer_set"],
                "peer_comparison": snapshot,
                "peer_set_status": snapshot["peer_set_status"],
                "valuation_confidence": 0.5,
            }
        )
        codes = {item["code"] for item in blockers}

        self.assertIn("PEER_COUNT_INSUFFICIENT", codes)
        self.assertTrue({"PEER_PRICE_MISSING", "PEER_FUNDAMENTALS_MISSING"} & codes)


if __name__ == "__main__":
    unittest.main()
