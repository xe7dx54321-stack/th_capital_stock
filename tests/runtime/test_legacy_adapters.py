from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from smr_app.adapters.agents import AgentRunRequest, load_agent_runs
from smr_app.adapters.decisions import DecisionContextRequest, load_decision_context
from smr_app.adapters.evidence import EvidenceRequest, load_evidence
from smr_app.adapters.fundamentals import FundamentalsRequest, load_fundamentals
from smr_app.adapters.risk import RiskContextRequest, load_risk_context
from smr_app.adapters.scheduler_jobs import SchedulerJobRequest, run_scheduler_job
from smr_app.adapters.valuation import ValuationRequest, load_valuation


ROOT = Path(__file__).resolve().parents[2]


class LegacyAdapterTests(unittest.TestCase):
    def test_new_runtime_does_not_import_phase_modules(self) -> None:
        adapter_root = ROOT / "smr_app" / "adapters"
        source = "\n".join(path.read_text(encoding="utf-8") for path in adapter_root.glob("*.py"))
        self.assertNotRegex(source, r"smr_phase[0-9]+")

    def test_evidence_adapter_returns_ticker_scoped_structured_rows(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.executescript(
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
                text_excerpt TEXT,
                url_or_doc_id TEXT,
                metadata_json TEXT,
                created_at TEXT,
                quality_score REAL,
                usable_for_core_claim INTEGER
            );
            CREATE TABLE research_claims (claim_id TEXT, ticker TEXT);
            CREATE TABLE claim_evidence_links (claim_id TEXT, evidence_id TEXT, relation_type TEXT, strength REAL);
            INSERT INTO evidence_items VALUES
                (1, 'ev_target', 'filing', 'official_filing', 'official', 'active', '2026-07-10', '2026-07-10',
                 'Revenue grew 20 percent.', 'doc-1', '{}', '2026-07-10', 0.9, 1),
                (2, 'ev_other', 'news', 'news', 'secondary', 'active', '2026-07-10', '2026-07-10',
                 'Unrelated.', 'doc-2', '{}', '2026-07-10', 0.5, 0);
            INSERT INTO research_claims VALUES ('claim_1', '300308.SZ');
            INSERT INTO claim_evidence_links VALUES ('claim_1', 'ev_target', 'supports', 0.9);
            """
        )

        result = load_evidence(conn, EvidenceRequest("300308.SZ", limit=10))

        self.assertTrue(result.ok)
        self.assertEqual(1, result.data["count"])
        self.assertEqual("ev_target", result.data["items"][0]["evidence_id"])
        conn.close()

    def test_fundamentals_and_valuation_adapters_use_stable_domain_modules(self) -> None:
        conn = sqlite3.connect(":memory:")
        self.assertEqual("missing", load_fundamentals(conn, FundamentalsRequest("300308.SZ")).status)
        conn.execute(
            """
            INSERT INTO fundamentals_snapshot(
                snapshot_id, ticker, market, period, revenue, source_evidence_ids_json,
                source_quality, freshness_status, confidence, missing_fields_json,
                field_details_json, field_missing_reasons_json, created_at, metadata_json
            ) VALUES ('f1', '300308.SZ', 'A', '2026Q1', 100.0, '["ev_f1"]',
                      'official', 'fresh', 0.9, '[]', '{}', '{}', '2026-07-10', '{}')
            """
        )
        self.assertEqual("ok", load_fundamentals(conn, FundamentalsRequest("300308.SZ")).status)

        self.assertEqual("missing", load_valuation(conn, ValuationRequest("300308.SZ")).status)
        conn.execute(
            """
            INSERT INTO valuation_snapshot(
                ticker, market, generated_at, valuation_available, current_price,
                peer_comparison_json, valuation_status, missing_data_json,
                allowed_usage, metadata_json, peer_set_json
            ) VALUES ('300308.SZ', 'A', '2026-07-10', 1, 42.0, '{}', 'available', '[]',
                      'research', '{}', '[]')
            """
        )
        self.assertEqual("ok", load_valuation(conn, ValuationRequest("300308.SZ")).status)
        conn.close()

    def test_risk_agent_and_decision_adapters_normalize_fake_database_rows(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.executescript(
            """
            CREATE TABLE risk_alert (
                alert_id INTEGER PRIMARY KEY, alert_time TEXT, alert_type TEXT, severity TEXT,
                ts_code TEXT, message TEXT, action TEXT, acknowledged INTEGER,
                lifecycle_status TEXT, occurrence_count INTEGER
            );
            INSERT INTO risk_alert VALUES
                (1, '2026-07-13', 'drawdown', 'warning', '300308.SZ', 'Drawdown', 'Review', 0, 'opened', 2);
            CREATE TABLE data_source_health (
                source_key TEXT, market TEXT, asset_type TEXT, data_type TEXT,
                last_success_at TEXT, last_data_timestamp TEXT, expected_update_frequency TEXT,
                freshness_status TEXT, stale_after_minutes INTEGER, blocking_level TEXT,
                staleness_reason TEXT, affected_modules_json TEXT, metadata_json TEXT, updated_at TEXT
            );
            INSERT INTO data_source_health VALUES
                ('daily_bar', 'A', 'stock', 'daily_bar', NULL, '2026-07-12', 'daily',
                 'fresh', 1440, 'none', NULL, '[]', '{"condition":"current"}', '2026-07-13');
            CREATE TABLE agent_runs (
                run_id TEXT, agent_or_script TEXT, entity_type TEXT, entity_id TEXT, status TEXT,
                started_at TEXT, completed_at TEXT, output_status TEXT, block_reasons_json TEXT,
                metadata_json TEXT, created_at TEXT
            );
            INSERT INTO agent_runs VALUES
                ('a1', 'research', 'ticker', '300308.SZ', 'success', '2026-07-13', '2026-07-13',
                 'ready', '[]', '{}', '2026-07-13');
            CREATE TABLE decision_ledger (
                decision_id TEXT, ticker TEXT, market TEXT, theme TEXT, action TEXT, status TEXT,
                decision_time TEXT, thesis_summary TEXT, evidence_ids_json TEXT,
                bear_case_summary TEXT, kill_conditions_json TEXT, risk_notes TEXT,
                human_review_status TEXT, outcome_status TEXT, metadata_json TEXT, updated_at TEXT
            );
            INSERT INTO decision_ledger VALUES
                ('d1', '300308.SZ', 'A', 'AI', 'watch', 'reviewed', '2026-07-12', 'Thesis',
                 '["ev_target"]', 'Bear', '["growth stalls"]', 'Risk', 'approved', 'pending', '{}', '2026-07-13');
            """
        )

        risk = load_risk_context(conn, RiskContextRequest("300308.SZ"))
        agents = load_agent_runs(conn, AgentRunRequest("300308.SZ"))
        decisions = load_decision_context(conn, DecisionContextRequest("300308.SZ"))

        self.assertEqual("drawdown", risk.data["alerts"][0]["alert_type"])
        self.assertEqual("a1", agents.data["items"][0]["run_id"])
        self.assertEqual(["ev_target"], decisions.data["items"][0]["evidence_ids"])
        conn.close()

    def test_scheduler_adapter_uses_current_python_without_shell_and_writes_full_log(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "adapter_echo.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("smr_app.adapters.scheduler_jobs.SCHEDULER_SCRIPT", fixture):
                result = run_scheduler_job(
                    SchedulerJobRequest(
                        job_id="fixture",
                        dry_run=True,
                        timeout_seconds=10,
                        artifact_dir=Path(temp_dir),
                    )
                )

            self.assertTrue(result.ok)
            self.assertEqual(sys.executable, result.data["command"][0])
            self.assertFalse(result.data["shell"])
            self.assertTrue(Path(result.data["log_path"]).exists())


if __name__ == "__main__":
    unittest.main()
