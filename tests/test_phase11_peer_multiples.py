import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_valuation import _peer_metric_summary


class Phase11PeerMultiplesTests(unittest.TestCase):
    def test_peer_metric_summary_requires_enough_peer_samples(self):
        summary = _peer_metric_summary(2.2, [{"pb": 3.0}], "pb", required=2)

        self.assertEqual(summary["status"], "missing")
        self.assertEqual(summary["reason"], "peer_metric_sample_insufficient")
        self.assertNotIn("peer_median", summary)

    def test_peer_metric_summary_outputs_median_and_percentile(self):
        summary = _peer_metric_summary(2.2, [{"pb": 2.0}, {"pb": 3.0}, {"pb": 4.0}], "pb", required=2)

        self.assertEqual(summary["status"], "available")
        self.assertEqual(summary["peer_median"], 3.0)
        self.assertEqual(summary["target_percentile_vs_peers"], 0.3333)


if __name__ == "__main__":
    unittest.main()
