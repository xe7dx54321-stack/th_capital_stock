from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from smr_app.adapters.fundamentals import FundamentalsRequest, load_fundamentals
from smr_app.adapters.risk import RiskContextRequest, load_risk_context
from smr_app.adapters.valuation import ValuationRequest, load_valuation
from smr_app.runtime.artifact_store import ArtifactStore
from smr_app.runtime.event_store import EventStore
from smr_app.runtime.migrations import apply_migrations
from smr_app.runtime.runner import WorkflowRunner
from smr_app.workflows.stock_deep_dive import stock_deep_dive_definition


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "stock_deep_dive"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def prepare_database(db_path: Path, fixture: dict | None) -> None:
    apply_migrations(db_path)
    conn = sqlite3.connect(db_path)
    ticker = fixture["ticker"] if fixture else "MISSING"
    load_fundamentals(conn, FundamentalsRequest(ticker))
    load_valuation(conn, ValuationRequest(ticker))
    load_risk_context(conn, RiskContextRequest(ticker))
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS evidence_items (
            id INTEGER PRIMARY KEY,
            evidence_id TEXT,
            source_key TEXT,
            source_type TEXT,
            source_quality TEXT,
            source_status TEXT,
            published_at TEXT,
            ingested_at TEXT,
            text_excerpt TEXT,
            url_or_doc_id TEXT,
            metadata_json TEXT,
            created_at TEXT,
            quality_score REAL,
            usable_for_core_claim INTEGER
        );
        CREATE TABLE IF NOT EXISTS research_claims (claim_id TEXT, ticker TEXT);
        CREATE TABLE IF NOT EXISTS claim_evidence_links (
            claim_id TEXT, evidence_id TEXT, relation_type TEXT, strength REAL
        );
        """
    )
    if fixture:
        conn.execute(
            """
            INSERT INTO evidence_items VALUES
                (1, ?, 'official_filing', 'official_filing', 'official', 'active',
                 '2026-07-10', '2026-07-10', ?, 'doc-1', ?, '2026-07-10', 0.95, 1)
            """,
            (fixture["evidence_id"], fixture["excerpt"], json.dumps({"ticker": fixture["ticker"]})),
        )
        conn.execute("INSERT INTO research_claims VALUES ('claim_fixture', ?)", (fixture["ticker"],))
        conn.execute(
            "INSERT INTO claim_evidence_links VALUES ('claim_fixture', ?, 'supports', 0.9)",
            (fixture["evidence_id"],),
        )
        conn.execute(
            """
            INSERT INTO fundamentals_snapshot(
                snapshot_id, ticker, market, period, revenue, operating_cash_flow,
                source_evidence_ids_json, source_quality, freshness_status, confidence,
                missing_fields_json, field_details_json, field_missing_reasons_json,
                created_at, metadata_json
            ) VALUES (?, ?, ?, '2026Q1', 100.0, 18.0, ?, 'official', 'fresh', 0.9,
                      '[]', '{}', '{}', '2026-07-10', '{}')
            """,
            (
                f"fund_{fixture['ticker']}",
                fixture["ticker"],
                fixture["market"],
                json.dumps([fixture["evidence_id"]]),
            ),
        )
        conn.execute(
            """
            INSERT INTO valuation_snapshot(
                ticker, market, generated_at, valuation_available, current_price, pe_ttm,
                peer_comparison_json, valuation_status, missing_data_json, allowed_usage,
                metadata_json, peer_set_json, valuation_confidence
            ) VALUES (?, ?, '2026-07-10', 1, 42.0, 25.0, '{}', 'available', '[]',
                      'research', '{}', '[]', 0.8)
            """,
            (fixture["ticker"], fixture["market"]),
        )
        conn.execute(
            """
            INSERT INTO data_source_health(
                source_key, market, asset_type, data_type, last_success_at,
                last_data_timestamp, expected_update_frequency, freshness_status,
                stale_after_minutes, blocking_level, staleness_reason,
                affected_modules_json, metadata_json, created_at, updated_at
            ) VALUES ('daily_bar', ?, 'stock', 'daily_bar', '2026-07-10', '2026-07-10',
                      'daily_close', 'fresh', 1440, 'none', NULL, '[]',
                      '{"condition":"current"}', '2026-07-10', '2026-07-10')
            """,
            (fixture["market"],),
        )
    conn.commit()
    conn.close()


class StockDeepDiveWorkflowTests(unittest.TestCase):
    def test_refresh_mode_runs_acquisition_preflight_without_aborting_research(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            db_path = root / "runtime.db"
            artifact_root = root / "artifacts"
            fixture = load_fixture("a_share.json")
            prepare_database(db_path, fixture)

            run = WorkflowRunner(db_path).run(
                stock_deep_dive_definition(artifact_root=artifact_root),
                {"ticker": fixture["ticker"], "allow_network": True},
                run_id="run_refresh_preflight",
            )

            self.assertEqual("completed", run["status"])
            packet = json.loads((artifact_root / run["run_id"] / "research_packet.json").read_text(encoding="utf-8"))
            acquisition = packet["research_v3"]["acquisition"]
            self.assertEqual("refresh_if_stale", acquisition["mode"])
            self.assertEqual(7, len(acquisition["manifest"]["requirements"]))
            self.assertEqual(7, acquisition["validation"]["total_requirements"])
            self.assertGreater(acquisition["validation"]["unresolved_requirements"], 0)

    def test_environment_source_database_is_separate_from_control_database(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            control_db_path = root / "control.db"
            source_db_path = root / "source.db"
            artifact_root = root / "artifacts"
            fixture = load_fixture("a_share.json")
            apply_migrations(control_db_path)
            prepare_database(source_db_path, fixture)

            with patch.dict("os.environ", {"SMR_SOURCE_DB_PATH": str(source_db_path)}):
                definition = stock_deep_dive_definition(artifact_root=artifact_root)
            run = WorkflowRunner(control_db_path).run(
                definition,
                {"ticker": fixture["ticker"], "allow_network": False},
                run_id="run_separate_source",
            )

            self.assertEqual("completed", run["status"])
            self.assertEqual("supported", run["summary"]["conclusion_status"])
            self.assertGreater(run["summary"]["evidence_count"], 0)

    def test_a_h_and_us_fixtures_create_cited_report_and_candidate_memory(self) -> None:
        for fixture_name in ("a_share.json", "hong_kong.json", "us_share.json"):
            with self.subTest(fixture=fixture_name), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                db_path = root / "runtime.db"
                artifact_root = root / "artifacts"
                fixture = load_fixture(fixture_name)
                prepare_database(db_path, fixture)

                run = WorkflowRunner(db_path).run(
                    stock_deep_dive_definition(artifact_root=artifact_root),
                    {"ticker": fixture["ticker"], "allow_network": False},
                    run_id=f"run_{fixture['market'].lower()}",
                )

                self.assertEqual("completed", run["status"])
                self.assertEqual("supported", run["summary"]["conclusion_status"])
                self.assertEqual("research_ready", run["summary"]["research_readiness"])
                self.assertEqual(3, len(run["summary"]["scenarios"]))
                self.assertTrue(run["summary"]["claims"])
                self.assertTrue(all(claim["evidence_ids"] for claim in run["summary"]["claims"]))
                self.assertTrue(all(claim["source_paths"] for claim in run["summary"]["claims"]))
                self.assertTrue(all(scenario["conditions"] for scenario in run["summary"]["scenarios"]))
                self.assertTrue(all(scenario["invalidation"] for scenario in run["summary"]["scenarios"]))
                self.assertEqual(2, len(run["summary"]["artifact_ids"]))
                conn = sqlite3.connect(db_path)
                try:
                    memory = conn.execute(
                        "SELECT status, source_run_id FROM memory_items WHERE memory_id=?",
                        (run["summary"]["memory_candidate_id"],),
                    ).fetchone()
                    self.assertEqual(("candidate", run["run_id"]), memory)
                    artifact_path = ArtifactStore(conn, [artifact_root]).resolve_artifact(
                        run["summary"]["artifact_ids"][0]
                    )
                    report = artifact_path.read_text(encoding="utf-8")
                    self.assertIn(fixture["evidence_id"], report)
                    self.assertIn("乐观情景", report)
                    self.assertIn("成立条件", report)
                    self.assertIn("失效条件", report)
                    self.assertIn("数据质量与隔离", report)
                    self.assertIn("本报告仅用于本地研究辅助", report)
                    packet_path = ArtifactStore(conn, [artifact_root]).resolve_artifact(
                        run["summary"]["artifact_ids"][1]
                    )
                    packet = json.loads(packet_path.read_text(encoding="utf-8"))
                    self.assertEqual("2.0", packet["schema_version"])
                    self.assertEqual("research_ready", packet["quality"]["readiness"])
                    self.assertEqual("research_ready", packet["quality"]["report_gate"]["report_status"])
                    self.assertEqual(1.0, packet["quality"]["report_gate"]["citation_coverage"])
                    self.assertEqual(fixture["evidence_id"], packet["quality"]["usable_evidence_ids"][0])
                    self.assertIn("valuation.current_price", packet["quality"]["quarantined_fields"])
                    self.assertTrue(all(
                        not set(claim["source_paths"]) & set(packet["quality"]["quarantined_fields"])
                        for claim in packet["claims"]
                    ))
                    event_types = [event["event_type"] for event in EventStore(conn).list_events(run["run_id"])]
                    self.assertIn("artifact.created", event_types)
                finally:
                    conn.close()

    def test_missing_evidence_fails_without_generating_a_fake_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            db_path = root / "runtime.db"
            prepare_database(db_path, None)

            run = WorkflowRunner(db_path).run(
                stock_deep_dive_definition(artifact_root=root / "artifacts"),
                {"ticker": "MISSING", "allow_network": False},
                run_id="run_missing",
            )

            self.assertEqual("failed", run["status"])
            self.assertEqual("RuntimeError", run["error_code"])
            self.assertIn("evidence floor not met", run["error_message"])
            self.assertEqual([], list((root / "artifacts").glob("**/stock_deep_dive.md")))

    def test_invalid_ticker_is_persisted_as_failed_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            db_path = root / "runtime.db"
            prepare_database(db_path, None)

            run = WorkflowRunner(db_path).run(
                stock_deep_dive_definition(artifact_root=root / "artifacts"),
                {"ticker": "../../bad", "allow_network": False},
                run_id="run_invalid",
            )

            self.assertEqual("failed", run["status"])
            self.assertEqual("ValueError", run["error_code"])


if __name__ == "__main__":
    unittest.main()
