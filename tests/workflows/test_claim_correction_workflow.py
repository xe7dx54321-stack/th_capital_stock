from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

from smr_app.runtime.runner import WorkflowRunner
from smr_app.workflows.claim_correction import claim_correction_definition


def _input() -> dict:
    return {
        "entity_key": "TEST.SZ",
        "allow_network": False,
        "claims": [
            {
                "claim_id": "market_cap",
                "claim_type": "fact",
                "metric": "market_cap",
                "value": 199.0,
                "unit": "亿元",
                "source": "旧行情快照",
                "evidence_id": "ev_old",
            },
            {
                "claim_id": "ruijie_network_market_cap",
                "claim_type": "fact",
                "metric": "ruijie_network_market_cap",
                "value": 300.0,
                "unit": "亿元",
                "source": "锐捷网络行情快照",
                "evidence_id": "ev_ruijie_market_cap",
            },
            {
                "claim_id": "holding_ratio",
                "claim_type": "fact",
                "metric": "holding_ratio",
                "value": 0.5,
                "unit": "比例",
                "source": "正式持股披露",
                "evidence_id": "ev_holding_ratio",
            },
            {
                "claim_id": "holding_value",
                "claim_type": "model",
                "metric": "holding_value",
                "value": 150.0,
                "unit": "亿元",
                "upstream_claim_ids": ["ruijie_network_market_cap", "holding_ratio"],
                "formula": "ruijie_network_market_cap * holding_ratio",
            },
            {
                "claim_id": "holding_discount",
                "claim_type": "output",
                "metric": "holding_discount",
                "value": 1 - 199.0 / 150.0,
                "unit": "比例",
                "upstream_claim_ids": ["market_cap", "holding_value"],
                "formula": "1 - market_cap / holding_value",
            },
            {
                "claim_id": "candidate_ranking_score",
                "claim_type": "model",
                "metric": "candidate_ranking_score",
                "value": 50.0 + (1 - 199.0 / 150.0) * 20.0,
                "unit": "分",
                "upstream_claim_ids": ["holding_discount"],
                "formula": "50 + holding_discount * 20",
            },
            {
                "claim_id": "conclusion_score",
                "claim_type": "output",
                "metric": "conclusion_score",
                "value": 50.0 + (1 - 199.0 / 150.0) * 20.0,
                "unit": "分",
                "upstream_claim_ids": ["candidate_ranking_score"],
                "formula": "candidate_ranking_score",
            },
        ],
        "correction": {
            "claim_id": "market_cap",
            "new_value": 260.0,
            "source": "交易所行情接口交叉核验",
            "evidence_id": "ev_authoritative_260",
        },
    }


def test_claim_correction_recomputes_every_dependent_claim_and_persists_audit() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        db_path = root / "runtime.db"
        artifact_root = root / "artifacts"
        runner = WorkflowRunner(db_path)
        result = runner.run(
            claim_correction_definition(artifact_root=artifact_root),
            _input(),
            run_id="run_generic_correction",
        )

        assert result["status"] == "completed", result
        assert result["summary"]["approved"] is True
        assert result["summary"]["changed_claim_count"] == 4

        diff_path = artifact_root / "run_generic_correction" / "correction_diff.json"
        payload = json.loads(diff_path.read_text(encoding="utf-8"))
        changes = {item["claim_id"]: item for item in payload["changes"]}
        assert changes["market_cap"]["new_value"] == 260.0
        assert round(changes["holding_discount"]["new_value"], 8) == round(1 - 260.0 / 150.0, 8)
        assert round(changes["candidate_ranking_score"]["new_value"], 8) == round(
            50.0 + (1 - 260.0 / 150.0) * 20.0,
            8,
        )
        assert changes["conclusion_score"]["new_value"] == changes["candidate_ranking_score"]["new_value"]
        assert all(payload["quality_checks"].values())

        conn = sqlite3.connect(db_path)
        try:
            assert conn.execute(
                "SELECT status FROM research_claim_corrections WHERE correction_id=?",
                ("correction_run_generic_correction",),
            ).fetchone() == ("applied",)
            assert conn.execute(
                "SELECT COUNT(*) FROM research_claim_versions WHERE source_run_id=?",
                ("run_generic_correction",),
            ).fetchone()[0] == 4
            artifact_types = {
                row[0]
                for row in conn.execute(
                    "SELECT artifact_type FROM workflow_artifacts WHERE run_id=?",
                    ("run_generic_correction",),
                )
            }
            assert artifact_types == {"correction_diff", "claim_correction_report"}
        finally:
            conn.close()


def test_claim_correction_blocks_when_downstream_cannot_be_recomputed() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        data = _input()
        data["claims"][4].pop("formula")
        result = WorkflowRunner(root / "runtime.db").run(
            claim_correction_definition(artifact_root=root / "artifacts"),
            data,
            run_id="run_block_stale_downstream",
        )

        assert result["status"] == "failed"
        assert "has no deterministic formula" in result["error_message"]
