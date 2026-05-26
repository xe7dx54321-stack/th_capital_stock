import json
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

from build_phase26_capacity_shipment_evidence import build_payload


def make_capacity_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE evidence_items (
            id INTEGER PRIMARY KEY,
            evidence_id TEXT,
            source_key TEXT,
            source_type TEXT,
            source_quality TEXT,
            published_at TEXT,
            text_excerpt TEXT,
            metadata_json TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO evidence_items VALUES (1, 'ev_capacity_1', 'filing', 'filing', 'medium', '2026-05-01', '300394.SZ 天孚通信 capacity expansion capex', ?)",
        (json.dumps({"ticker": "300394.SZ"}),),
    )
    return conn


class Phase26CapacityShipmentEvidenceTests(unittest.TestCase):
    def test_capacity_is_not_shipment(self):
        payload = build_payload(make_capacity_conn(), ticker="300394.SZ")
        pack = payload["capacity_shipment_evidence"]
        self.assertEqual(pack["evidence_status"], "partial")
        self.assertEqual(len(pack["capacity_expansion_evidence"]), 1)
        self.assertEqual(pack["shipment_evidence"], [])
        self.assertIn("capex or capacity expansion is not shipment", pack["limitations"])


if __name__ == "__main__":
    unittest.main()
