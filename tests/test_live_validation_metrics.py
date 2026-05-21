import json
import sqlite3
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
for path in (LIB_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from smr_claim_graph import ensure_claim_graph_tables, upsert_evidence
from smr_news_ingestion import ensure_news_tables
from validate_live_news_ingestion import summarize_ticker


class LiveValidationMetricsTests(unittest.TestCase):
    def test_live_news_summary_counts_only_matching_current_news_evidence(self):
        conn = sqlite3.connect(":memory:")
        ensure_news_tables(conn)
        ensure_claim_graph_tables(conn)
        now = datetime.now()
        today = now.strftime("%Y-%m-%d %H:%M:%S")
        old_day = (now - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            """
            INSERT INTO news_items (
                news_id, source_key, source_name, title, body, url, published_at, ingested_at,
                tickers_json, themes_json, entities_json, language, market, credibility,
                dedupe_hash, title_fingerprint, source_list_json, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '[]', '[]', 'en', 'A', 'medium', ?, ?, ?, ?)
            """,
            (
                "news-live-current",
                "yahoo_finance_rss",
                "Yahoo",
                "000001.SZ current live news",
                "fresh body",
                "https://example.com/current",
                today,
                today,
                json.dumps(["000001.SZ"]),
                "hash-current",
                "fingerprint-current",
                json.dumps(["yahoo_finance_rss"]),
                json.dumps({"live": True, "ticker": "000001.SZ"}),
            ),
        )
        conn.execute(
            """
            INSERT INTO news_items (
                news_id, source_key, source_name, title, body, url, published_at, ingested_at,
                tickers_json, themes_json, entities_json, language, market, credibility,
                dedupe_hash, title_fingerprint, source_list_json, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '[]', '[]', 'en', 'A', 'medium', ?, ?, ?, ?)
            """,
            (
                "news-live-old",
                "yahoo_finance_rss",
                "Yahoo",
                "000001.SZ old live news",
                "old body",
                "https://example.com/old",
                old_day,
                old_day,
                json.dumps(["000001.SZ"]),
                "hash-old",
                "fingerprint-old",
                json.dumps(["yahoo_finance_rss"]),
                json.dumps({"live": True, "ticker": "000001.SZ"}),
            ),
        )
        upsert_evidence(
            conn,
            {
                "evidence_id": "ev-current",
                "source_key": "yahoo_finance_rss",
                "source_type": "news",
                "source_quality": "secondary",
                "source_status": "active",
                "published_at": today,
                "ingested_at": today,
                "text_excerpt": "000001.SZ current live news",
                "url_or_doc_id": "https://example.com/current",
                "metadata": {"live": True, "news_id": "news-live-current", "ticker": "000001.SZ", "tickers": ["000001.SZ"]},
            },
        )
        upsert_evidence(
            conn,
            {
                "evidence_id": "ev-old",
                "source_key": "yahoo_finance_rss",
                "source_type": "news",
                "source_quality": "secondary",
                "source_status": "active",
                "published_at": old_day,
                "ingested_at": old_day,
                "text_excerpt": "000001.SZ old live news",
                "url_or_doc_id": "https://example.com/old",
                "metadata": {"live": True, "news_id": "news-live-old", "ticker": "000001.SZ", "tickers": ["000001.SZ"]},
            },
        )
        upsert_evidence(
            conn,
            {
                "evidence_id": "ev-loose-match",
                "source_key": "yahoo_finance_rss",
                "source_type": "news",
                "source_quality": "secondary",
                "source_status": "active",
                "published_at": today,
                "ingested_at": today,
                "text_excerpt": "loose ticker mention should not count",
                "url_or_doc_id": "https://example.com/loose",
                "metadata": {"live": True, "news_id": "news-other", "ticker": "000001.SZ", "tickers": ["000001.SZ"]},
            },
        )

        since_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        result = summarize_ticker(conn, "000001.SZ", since_date)

        self.assertEqual(result["news_items_found"], 1)
        self.assertEqual(result["evidence_items_created"], 1)
        self.assertEqual(result["claim_links_created"], 1)


if __name__ == "__main__":
    unittest.main()
