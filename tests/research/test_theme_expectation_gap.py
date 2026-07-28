"""
阶段 7「主题预期差筛选 V1」单元测试

小白讲解：
    验证 3 件事：
        1. 最小输入能跑完整 8 阶段 → 状态 completed，生成 4 个制品
        2. 质量门：data_completeness<0.3 的股不会强推 strong_focus
        3. 候选全集透明：被排除清单都带理由，不会"偷偷漏掉某只"
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from smr_app.runtime.contracts import WorkflowContext
from smr_app.runtime.migrations import apply_migrations
from smr_app.runtime.registry import production_registry
from smr_app.runtime.runner import WorkflowRunner
from smr_app.workflows.theme_expectation_gap import _get_default_artifact_root


class ThemeExpectationGapSmokeTests(unittest.TestCase):
    """最小烟测 + 质量门 + 透明性"""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp.name)
        self.db_path = self.temp_path / "runtime.db"
        apply_migrations(self.db_path)
        self.runner = WorkflowRunner(self.db_path)
        self.artifacts_root = self.temp_path / "artifacts"
        self.artifacts_root.mkdir(parents=True, exist_ok=True)
        self._prev = os.environ.get("SMR_ARTIFACT_ROOTS")
        os.environ["SMR_ARTIFACT_ROOTS"] = str(self.artifacts_root)
        # memory root 也临时切，避免污染用户目录
        self._prev_mem = os.environ.get("SMR_MEMORY_ROOT")
        os.environ["SMR_MEMORY_ROOT"] = str(self.temp_path / "memory")
        self.definition = production_registry().get("theme_expectation_gap")

    def tearDown(self) -> None:
        if self._prev is None:
            os.environ.pop("SMR_ARTIFACT_ROOTS", None)
        else:
            os.environ["SMR_ARTIFACT_ROOTS"] = self._prev
        if self._prev_mem is None:
            os.environ.pop("SMR_MEMORY_ROOT", None)
        else:
            os.environ["SMR_MEMORY_ROOT"] = self._prev_mem
        self.temp.cleanup()

    # ------------------------------------------------------------------
    @staticmethod
    def _fixture_input() -> dict:
        """最小合法输入：AI 算力 5 只候选，含 1 只明显纯、其他不纯"""
        return {
            "theme_name": "AI 算力基础设施",
            "theme_id": "ai_compute_infra",
            "raw_candidates": [
                {"ticker": "300308.SZ", "name": "中际旭创", "business_purity": 0.92, "revenue_sensitivity": 0.95,
                 "tags": ["光模块", "AI", "800G"], "note": "AI 光模块龙头"},
                {"ticker": "002281.SZ", "name": "光迅科技", "business_purity": 0.70, "revenue_sensitivity": 0.65,
                 "tags": ["光模块", "光器件"], "note": "数通+运营商"},
                {"ticker": "603019.SH", "name": "中科曙光", "business_purity": 0.85, "revenue_sensitivity": 0.80,
                 "tags": ["服务器", "AI"], "note": "AI 服务器"},
                {"ticker": "601138.SH", "name": "工业富联", "business_purity": 0.35, "revenue_sensitivity": 0.40,
                 "tags": ["代工", "服务器"], "note": "业务杂，消费电子占比高"},
                {"ticker": "000063.SZ", "name": "中兴通讯", "business_purity": 0.30, "revenue_sensitivity": 0.30,
                 "tags": ["运营商设备"], "note": "运营商为主，AI 业务纯度低"},
            ],
            "keyword_hint_list": ["AI", "算力", "800G", "服务器", "光模块"],
            "market_overrides": {
                "300308.SZ": {"market_cap_yi": 1500.0, "avg_turnover_yi": 35.0},
                "002281.SZ": {"market_cap_yi": 500.0, "avg_turnover_yi": 10.0},
                "603019.SH": {"market_cap_yi": 800.0, "avg_turnover_yi": 18.0},
                "601138.SH": {"market_cap_yi": 5000.0, "avg_turnover_yi": 25.0},
                "000063.SZ": {"market_cap_yi": 1800.0, "avg_turnover_yi": 12.0},
            },
            "evidence_overrides": {
                "300308.SZ": {"bullish_ratio": 0.65, "implied_cagr": 0.35, "guided_cagr": 0.45,
                               "pe_ttm": 30.0, "pb_mrq": 5.0, "turnover_20d": 0.05,
                               "catalysts": ["400G/800G 出货放量", "北美云厂资本开支持续"],
                               "risks": ["汇率波动", "客户集中度高"],
                               "catalyst_count": 2, "catalysts_verified": 1, "risk_count": 2},
                "002281.SZ": {"bullish_ratio": 0.55, "implied_cagr": 0.22, "guided_cagr": 0.25,
                               "pe_ttm": 28.0, "pb_mrq": 3.5, "turnover_20d": 0.03,
                               "catalysts": ["1.6T 研发进度"], "risks": ["数通份额提升慢"],
                               "catalyst_count": 1, "catalysts_verified": 0, "risk_count": 1},
                "603019.SH": {"bullish_ratio": 0.45, "implied_cagr": 0.20, "guided_cagr": 0.30,
                               "pe_ttm": 40.0, "pb_mrq": 4.5, "turnover_20d": 0.04,
                               "catalysts": ["国产服务器出货"], "risks": ["美光制裁风险", "毛利率低"],
                               "catalyst_count": 1, "catalysts_verified": 0, "risk_count": 2},
                "601138.SH": {"bullish_ratio": 0.30, "implied_cagr": 0.08, "guided_cagr": 0.10,
                               "pe_ttm": 15.0, "pb_mrq": 2.5, "turnover_20d": 0.01,
                               "catalysts": [], "risks": ["消费电子下滑"],
                               "catalyst_count": 0, "catalysts_verified": 0, "risk_count": 1},
                "000063.SZ": {"bullish_ratio": 0.25, "implied_cagr": 0.05, "guided_cagr": 0.08,
                               "pe_ttm": 12.0, "pb_mrq": 1.5, "turnover_20d": 0.005,
                               "catalysts": [], "risks": [],
                               "catalyst_count": 0, "catalysts_verified": 0, "risk_count": 0},
            },
            "allow_network": False,
        }

    # ------------------------------------------------------------------
    def test_registry_produces_enabled_workflow_with_8_stages(self) -> None:
        self.assertEqual("theme_expectation_gap", self.definition.workflow_id)
        self.assertEqual(8, len(self.definition.stages))

    def test_workflow_artifact_root_override_works(self) -> None:
        self.assertEqual(self.artifacts_root, _get_default_artifact_root())

    def test_smoke_full_run_status_completed_and_4_artifacts_exist(self) -> None:
        """阶段 7 核心烟测：8 阶段跑通，4 个制品都在"""
        run = self.runner.run(self.definition, self._fixture_input(), run_id="gap_001")

        self.assertEqual("completed", run["status"],
                         f"期望 completed，实际 {run['status']}；错误：{run.get('error_message') or ''}")
        # 检查 4 个制品：找到输出目录（最后一个 stage 的 artifacts）
        out_dir_str = (run.get("summary") or {}).get("out_dir") or \
                      self._find_last_out_dir("theme_expectation_gap_")
        self.assertIsNotNone(out_dir_str, "未找到 out_dir")
        out_dir = Path(str(out_dir_str))
        self.assertTrue((out_dir / "theme_universe.json").exists(), "缺 theme_universe.json")
        self.assertTrue((out_dir / "expectation_scores.json").exists(), "缺 expectation_scores.json")
        self.assertTrue((out_dir / "candidate_matrix.md").exists(), "缺 candidate_matrix.md")
        self.assertTrue((out_dir / "watch_list.csv").exists(), "缺 watch_list.csv")
        # 读 JSON，合法性检查
        scores = json.loads((out_dir / "expectation_scores.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(scores), 3, "至少入选 3 只（300308/002281/603019）")
        # 首名应当是 300308（纯度+催化+预期差都最高）
        top1 = scores[0]
        self.assertEqual("300308.SZ", top1["ticker"], f"第一名应当是中际旭创，但实际：{top1['ticker']}")

    def test_excluded_list_transparent_each_entry_has_reason(self) -> None:
        """透明性：被排除清单里的每一只都有非空 exclude_reason"""
        self.runner.run(self.definition, self._fixture_input(), run_id="gap_002")
        out_dir = Path(self._find_last_out_dir("theme_expectation_gap_"))
        univ = json.loads((out_dir / "theme_universe.json").read_text(encoding="utf-8"))
        excluded = univ.get("excluded") or []
        # fixture 里没硬写 inclusion_rules 的严格阈值，最少要保证 excluded 内元素都是合法结构
        for ex in excluded:
            self.assertIn("ticker", ex, "excluded 里缺少 ticker 字段")
            self.assertTrue(
                ex.get("exclude_reason") is not None and str(ex["exclude_reason"]) != "",
                f"excluded ticker {ex.get('ticker')} exclude_reason 为空，违反透明性"
            )

    def test_quality_gate_low_completeness_not_strong_focus(self) -> None:
        """质量门：数据完整性低的股票不会被评 strong_focus"""
        inp = self._fixture_input()
        # 手动塞一个 data_completeness 很低的（不填 evidence & market）
        inp["raw_candidates"].append({
            "ticker": "000001.SZ", "name": "平安银行", "tags": ["银行"],
        })
        inp["market_overrides"]["000001.SZ"] = {}
        inp["evidence_overrides"]["000001.SZ"] = {}
        self.runner.run(self.definition, inp, run_id="gap_003")
        out_dir = Path(self._find_last_out_dir("theme_expectation_gap_"))
        scores = json.loads((out_dir / "expectation_scores.json").read_text(encoding="utf-8"))
        bank = next((s for s in scores if s["ticker"] == "000001.SZ"), None)
        if bank is not None:
            self.assertNotEqual(
                "strong_focus", bank["recommendation"],
                f"数据残缺的银行股不应评 strong_focus，实际：{bank['recommendation']}"
            )
            self.assertTrue(bank["degraded"], "数据残缺股应该标记 degraded=True")

    def test_validate_inputs_rejects_network_mode(self) -> None:
        """阶段 1 校验：allow_network=True 必须 fail"""
        bad = self._fixture_input()
        bad["allow_network"] = True
        run = self.runner.run(self.definition, bad, run_id="gap_004_net")
        self.assertEqual("failed", run["status"], "allow_network=True 必须失败")

    def test_workflow_reports_every_stage_status(self) -> None:
        """8 个阶段都应当是 completed/degraded，不能出现 failed"""
        run = self.runner.run(self.definition, self._fixture_input(), run_id="gap_005")
        stage_results = run.get("stages") or {}
        for stage_id, st in stage_results.items():
            self.assertIn(
                st.get("status"), {"completed", "degraded"},
                f"阶段 {stage_id} 状态 {st.get('status')} 异常，message={st.get('message')}"
            )

    # ------------------------------------------------------------------
    def _find_last_out_dir(self, prefix: str) -> str:
        """找到最新的输出目录（按 mtime）"""
        candidates = [p for p in self.artifacts_root.iterdir()
                      if p.is_dir() and p.name.startswith(prefix)]
        if not candidates:
            return ""
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return str(candidates[0])


if __name__ == "__main__":
    unittest.main()
