import json
import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_end_demand_proxy import build_end_demand_proxy


def make_evidence_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE evidence_items (
            id INTEGER PRIMARY KEY,
            evidence_id TEXT,
            source_key TEXT,
            source_type TEXT,
            source_quality TEXT,
            source_status TEXT,
            published_at TEXT,
            ingested_at TEXT,
            created_at TEXT,
            text_excerpt TEXT,
            metadata_json TEXT
        )
        """
    )
    conn.execute(
        """
        INSERT INTO evidence_items VALUES (
            1, 'ev_ai_optical_1', 'news_ai_optical', 'news', 'medium', 'active',
            '2026-05-20', '2026-05-20', '2026-05-20',
            'AI data center capex growth drives strong optical module and 800G demand',
            ?
        )
        """,
        (json.dumps({}),),
    )
    return conn


class Phase25EndDemandProxyTests(unittest.TestCase):
    def test_end_demand_proxy_uses_active_evidence_but_not_company_order(self):
        conn = make_evidence_conn()
        payload = build_end_demand_proxy(conn, "ai_optical_interconnect")
        proxy = payload["end_demand_proxy"]
        self.assertEqual(proxy["overall_direction"], "positive")
        self.assertGreater(proxy["active_evidence_count"], 0)
        self.assertFalse(proxy["safety"]["industry_proxy_treated_as_company_order"])
        self.assertFalse(proxy["safety"]["planned_source_used_as_active_evidence"])
        driver_without_evidence = next(item for item in proxy["drivers"] if not item["evidence_ids"])
        self.assertEqual(driver_without_evidence["allowed_usage"], "context_only")


if __name__ == "__main__":
    unittest.main()
