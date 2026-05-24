import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_consensus_proxy import build_consensus_revision_proxy
from smr_valuation import build_forward_eps_snapshot


class Phase10ForwardEpsProxyTests(unittest.TestCase):
    def test_proxy_eps_is_internal_and_evidence_linked(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE evidence_items (evidence_id TEXT, source_key TEXT)")
        conn.execute("INSERT INTO evidence_items VALUES ('ev-1', 'filing')")
        build_consensus_revision_proxy(conn, "09988.HK EPS 7.10 -> 8.32 raised higher", ["ev-1"], "09988.HK")

        forward_eps = build_forward_eps_snapshot(conn, "09988.HK", {})

        self.assertEqual(forward_eps["status"], "proxy")
        self.assertEqual(forward_eps["source"], "internal_proxy")
        self.assertFalse(forward_eps["is_official_consensus"])
        self.assertEqual(forward_eps["source_evidence_ids"], ["ev-1"])

    def test_missing_proxy_eps_does_not_impersonate_consensus(self):
        conn = sqlite3.connect(":memory:")
        forward_eps = build_forward_eps_snapshot(conn, "09988.HK", {"eps_diluted": 5.5})

        self.assertEqual(forward_eps["status"], "proxy")
        self.assertEqual(forward_eps["source"], "fundamentals_eps_proxy")
        self.assertEqual(forward_eps["allowed_usage"], "context_only")
        self.assertFalse(forward_eps["is_official_consensus"])


if __name__ == "__main__":
    unittest.main()
