import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
JOBS_DIR = ROOT / "08_scripts" / "jobs"
for path in (LIB_DIR, JOBS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_peer_valuation_data import peer_blockers
from smr_valuation import peer_set_definition


class Phase11PeerDataCompletionTests(unittest.TestCase):
    def test_09988_peer_set_loads(self):
        peer_set_id, peer_set = peer_set_definition("09988.HK")

        self.assertEqual(peer_set_id, "hk_internet_platforms")
        self.assertIn("00700.HK", peer_set["tickers"])

    def test_required_peer_count_clears_remaining_peer_blockers(self):
        blockers = peer_blockers(
            {
                "peer_set_status": "available",
                "peer_count_available": 2,
                "peer_count_required": 2,
                "peer_missing_reasons": ["peer_price_missing"],
            }
        )

        self.assertEqual(blockers, [])

    def test_peer_count_insufficient_remains_specific(self):
        blockers = peer_blockers(
            {
                "peer_set_status": "partial",
                "peer_count_available": 1,
                "peer_count_required": 2,
                "peer_missing_reasons": ["peer_price_missing", "peer_multiples_missing"],
            }
        )

        self.assertIn("PEER_PRICE_MISSING", blockers)
        self.assertIn("PEER_MULTIPLES_MISSING", blockers)


if __name__ == "__main__":
    unittest.main()
