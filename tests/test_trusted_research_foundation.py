import sqlite3
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_claim_graph import build_claim_evidence_graph, claim_graph_summary
from smr_consensus_proxy import build_consensus_revision_proxy
from smr_data_health import check_freshness_gate, refresh_system_data_health
from smr_decision import (
    current_decision_status,
    review_recommendation,
    submit_for_human_review,
    upsert_decision_ledger,
)
from smr_market_calendar import get_expected_latest_trading_day
from smr_research_quality import check_report_evidence, lint_report


def make_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE daily_bar (
            ts_code TEXT,
            market TEXT,
            trade_date TEXT,
            close REAL
        );
        CREATE TABLE us_daily_bar (
            symbol TEXT,
            trade_date TEXT,
            close REAL
        );
        CREATE TABLE factor_daily (
            ts_code TEXT,
            trade_date TEXT,
            factor_name TEXT,
            factor_value REAL
        );
        CREATE TABLE market_event (
            entity_id TEXT,
            event_family TEXT,
            event_type TEXT,
            source_kind TEXT,
            publish_time TEXT,
            created_at TEXT
        );
        CREATE TABLE source_manifest (
            source_type TEXT,
            status TEXT,
            entity_id TEXT,
            updated_at TEXT,
            created_at TEXT,
            metadata_json TEXT
        );
        """
    )
    return conn


class FreshnessGateTests(unittest.TestCase):
    def test_stale_daily_bar_blocks_opportunity_radar(self):
        conn = make_conn()
        conn.execute("INSERT INTO daily_bar VALUES ('000001.SZ', 'A', '2000-01-01', 1.0)")
        conn.execute("INSERT INTO daily_bar VALUES ('09988.HK', 'H', '2000-01-01', 1.0)")
        conn.execute("INSERT INTO us_daily_bar VALUES ('BABA', '2000-01-01', 1.0)")
        refresh_system_data_health(conn)

        gate = check_freshness_gate(
            conn,
            module_name="opportunity_radar",
            required_data_types=["daily_bar"],
            allow_degraded=False,
            refresh=False,
        )

        self.assertEqual(gate.status, "block")
        self.assertNotIn("generate_recommendation_candidate", gate.allowed_actions)

    def test_consensus_revision_planned_is_missing_not_evidence(self):
        conn = make_conn()
        today = datetime.now().strftime("%Y-%m-%d")
        conn.execute("INSERT INTO daily_bar VALUES ('000001.SZ', 'A', ?, 1.0)", (today,))
        conn.execute("INSERT INTO daily_bar VALUES ('09988.HK', 'H', ?, 1.0)", (today,))
        conn.execute("INSERT INTO us_daily_bar VALUES ('BABA', ?, 1.0)", (today,))
        snapshot = refresh_system_data_health(conn)

        consensus_rows = [row for row in snapshot["items"] if row["data_type"] == "consensus_revision"]
        self.assertTrue(consensus_rows)
        self.assertIn(consensus_rows[0]["freshness_status"], {"planned", "disabled"})
        self.assertEqual(consensus_rows[0]["blocking_level"], "degrade")

    def test_market_calendar_handles_weekend_and_us_holiday(self):
        self.assertEqual(
            get_expected_latest_trading_day("A", datetime(2026, 5, 23, 12, 0)).isoformat(),
            "2026-05-22",
        )
        self.assertEqual(
            get_expected_latest_trading_day("US", datetime(2026, 5, 26, 8, 0)).isoformat(),
            "2026-05-22",
        )

    def test_capability_matrix_allows_static_research_with_stale_daily_bar(self):
        conn = make_conn()
        today = datetime.now().strftime("%Y-%m-%d")
        conn.execute("INSERT INTO daily_bar VALUES ('000001.SZ', 'A', '2000-01-01', 1.0)")
        conn.execute("INSERT INTO daily_bar VALUES ('09988.HK', 'H', '2000-01-01', 1.0)")
        conn.execute("INSERT INTO us_daily_bar VALUES ('BABA', '2000-01-01', 1.0)")
        conn.execute("INSERT INTO factor_daily VALUES ('000001.SZ', ?, 'pe_ttm', 10.0)", (today,))
        conn.execute("INSERT INTO market_event VALUES ('evt-1', 'company_event', 'announcement', 'announcement', ?, ?)", (today, today))
        snapshot = refresh_system_data_health(conn)
        capabilities = snapshot.get("capability_status") or {}
        self.assertEqual(capabilities["static_company_research"]["status"], "allowed_with_warning")
        self.assertEqual(capabilities["recommendation_candidate"]["status"], "blocked")


class ResearchQualityTests(unittest.TestCase):
    def test_buy_without_counter_evidence_is_blocked(self):
        result = check_report_evidence(
            "建议买入 XXX。核心逻辑是需求显著受益。",
            dashboard_summary={"action": "买入 XXX", "portfolio_action_plan": {"initial_action": {"buy": {"amount_cny": 10000}}}},
            evidence_pack_text="# Evidence\nsource_path_count: `5`\n官方公告 SEC 公司 IR",
        )
        self.assertEqual(result.severity, "block")
        self.assertFalse(result.recommendation_allowed)
        self.assertTrue(result.missing_counter_evidence)

    def test_linter_blocks_placeholder_text(self):
        lint = lint_report(
            "## 报告\n这里填写后续逻辑。TBD",
            dashboard_summary={},
            freshness_gate_result={"status": "pass"},
            evidence_check_result={"severity": "pass", "recommendation_allowed": False},
        )
        self.assertEqual(lint.allowed_publish_status, "blocked")
        self.assertFalse(lint.passed)

    def test_linter_blocks_consensus_revision_claim_when_disabled(self):
        lint = lint_report(
            "市场预期已经上修，因此建议继续推进。",
            dashboard_summary={},
            freshness_gate_result={"status": "pass"},
            evidence_check_result={"severity": "pass", "recommendation_allowed": False},
        )
        codes = {issue["code"] for issue in lint.issues}
        self.assertIn("consensus_claim_without_source", codes)

    def test_linter_blocks_action_when_freshness_gate_stale(self):
        lint = lint_report(
            "建议买入 XXX，仓位 5%，反方观点是估值高，证伪条件是跌破均线，风险是波动。",
            dashboard_summary={"action": "买入 XXX", "portfolio_action_plan": {"initial_action": {"buy": {"amount_cny": 10000}}}},
            freshness_gate_result={"status": "block"},
            evidence_check_result={"severity": "pass", "recommendation_allowed": True},
        )
        codes = {issue["code"] for issue in lint.issues}
        self.assertIn("action_with_stale_data", codes)

    def test_linter_allows_internal_consensus_proxy_wording(self):
        lint = lint_report(
            "内部代理指标显示预期可能上修，但这不是正式一致预期。",
            dashboard_summary={},
            freshness_gate_result={"status": "pass"},
            evidence_check_result={"severity": "pass", "recommendation_allowed": False},
        )
        codes = {issue["code"] for issue in lint.issues}
        self.assertNotIn("consensus_claim_without_source", codes)


class ClaimGraphTests(unittest.TestCase):
    def test_core_claim_links_to_evidence_ids(self):
        conn = sqlite3.connect(":memory:")
        summary = {"action_detail": "建议观察 000001.SZ", "confidence_rationale": "需求改善带来收入增长弹性。"}
        build_claim_evidence_graph(
            conn,
            report_id="report-1",
            recommendation_id="rec-1",
            report_text="因此判断需求改善可以带来收入增长。",
            evidence_pack_text=(
                "证据一：公司官方公告显示订单改善，并且管理层说明下游需求正在持续恢复。\n"
                "证据二：SEC filing 提到收入增长和订单能见度改善，能够作为独立交叉验证。"
            ),
            dashboard_summary=summary,
        )
        summary_result = claim_graph_summary(conn, "report-1")
        self.assertGreaterEqual(summary_result["total_core_claims"], 1)
        self.assertEqual(summary_result["unsupported_core_claims"], [])

    def test_consensus_proxy_is_not_official(self):
        conn = sqlite3.connect(":memory:")
        proxy = build_consensus_revision_proxy(
            conn,
            "000001.SZ 研报 EPS 2026E 上修，目标价提高。",
            evidence_ids=["ev-1"],
        )
        self.assertFalse(proxy["is_official_consensus"])
        self.assertEqual(proxy["proxy_direction"], "up")


class DecisionLedgerTests(unittest.TestCase):
    def test_ledger_and_human_review_flow(self):
        conn = sqlite3.connect(":memory:")
        upsert_decision_ledger(
            conn,
            recommendation_id="rec-1",
            status="pending_human_review",
            dashboard_summary={
                "action": "买入 000001.SZ",
                "portfolio_action_plan": {"initial_action": {"buy": {"amount_cny": 10000}}},
                "kill_triggers": ["跌破失效价"],
            },
            data_health_snapshot={"overall_status": "fresh", "items": []},
            evidence_check_snapshot={"severity": "pass"},
            lint_snapshot={"max_severity": "info"},
        )
        self.assertEqual(current_decision_status(conn, "rec-1"), "pending_human_review")

        review = review_recommendation(conn, "rec-1", "tester", "approve_paper", "证据足够，纸面通过。")
        self.assertEqual(review["new_status"], "approved_paper")
        self.assertEqual(current_decision_status(conn, "rec-1"), "approved_paper")

    def test_submit_for_human_review_records_review_row(self):
        conn = sqlite3.connect(":memory:")
        upsert_decision_ledger(conn, "rec-2", "candidate_shadow", dashboard_summary={"action": "观察"})
        submit_for_human_review(conn, "rec-2")
        row = conn.execute("SELECT COUNT(*) FROM recommendation_reviews WHERE recommendation_id='rec-2'").fetchone()
        self.assertEqual(row[0], 1)
        self.assertEqual(current_decision_status(conn, "rec-2"), "pending_human_review")

    def test_review_requires_comment_and_blocks_approving_blocked_item(self):
        conn = sqlite3.connect(":memory:")
        upsert_decision_ledger(conn, "rec-3", "blocked_by_data", dashboard_summary={"action": "买入 000001.SZ"})
        with self.assertRaises(ValueError):
            review_recommendation(conn, "rec-3", "tester", "approve_paper", "强行通过。")
        with self.assertRaises(ValueError):
            review_recommendation(conn, "rec-3", "tester", "archive", "")


if __name__ == "__main__":
    unittest.main()
