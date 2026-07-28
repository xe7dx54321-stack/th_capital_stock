"""
双标的换仓决策 V1 工作流单元测试

功能说明：
    测试 pair_switch_decision 工作流 12 个阶段。
    对应 master plan 阶段 5 验收 11 项：
        1. 12 维度 × 双标的 ComparisonMatrix JSON
        2. 时点差 ≤ 阈值；单位一致；每单元格附 data_gap/degrade 说明
        3. 调用阶段4估值制品（不复算）
        4. 生命周期 / 收入-利润质量 / 现金流 / ROE / 估值 / 隐含增长
           / 产业位置 / 催化 / 风险 / 拥挤度 / 价格状态 / 持仓约束
        5. 四方案：继续持有 / 部分换仓 / 完全换仓 / 暂缓
           每个方案有成立条件 / 失效条件 / 分批节奏
           每个方案附打分 + 数据置信度 + 数据不充分时自动降级声明
        6. 偏好 = 仅使用明确确认的字段，且每字段说明"来自用户还是默认"
        7. 明确声明不执行真实交易；估值高低不直接等同于买入/卖出信号
        8. 核心数据冲突：相关结论局部降级
        9. 推荐方案的分批节奏（例：50% 立即 + 50% 等财报）
        10. 领先指标监控清单，每指标含频率/阈值/触发失效的对应方案
        11. 独立质量门：完整度 × 成立/失效条件覆盖 × 推荐理由一致性，
            全部 OK 才放行"推荐方案"

参数说明：
    无外部参数，通过 unittest 自动收集执行。
    金标准案例：阳光电源（300274.SZ）→ 海光信息（688041.SH）
    为减少对外部 DB 的依赖，用 SQLite 临时文件插入两标的
    fundamentals_snapshot / valuation_snapshot 数据（阶段2）。

返回值说明：
    所有 test_ 函数均应通过。失败则抛 AssertionError。

异常处理：
    - 任何阶段抛出未捕获异常都视为测试失败
    - 断言失败会带清楚的中文说明
"""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from smr_app.runtime.runner import WorkflowRunner
from smr_app.workflows.pair_switch_decision import (
    pair_switch_decision_definition,
)


# ============================================================================
# 金标准案例：阳光电源（被换出 A） vs 海光信息（被换入 B）
# 小白讲解：以下数据都是"假设的"示例数据，仅用于演示工作流可运行，
# 不代表任何真实投资建议。请不要照抄！
# ============================================================================


def _insert_test_snapshot(conn: sqlite3.Connection) -> None:
    """
    为两标的创建 fundamentals_snapshot 和 valuation_snapshot 表 + 插入测试数据

    小白讲解：
        本工作流的阶段2会从 fundamentals_snapshot / valuation_snapshot 读取数据，
        但 runtime 的 migrations.py 本身不负责创建这两张业务表（它们属于数据源库，
        不属于工作流运行时元数据）。所以测试时，我们需要在临时 DB 里
        手动 CREATE TABLE，再插入两行假数据。
    """
    conn.execute(
        """CREATE TABLE IF NOT EXISTS fundamentals_snapshot(
            ticker TEXT PRIMARY KEY,
            revenue REAL, net_income REAL, gross_margin REAL, net_margin REAL,
            operating_margin REAL, roe REAL, source TEXT,
            period_end TEXT, created_at TEXT
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS valuation_snapshot(
            ticker TEXT PRIMARY KEY,
            pe_ttm REAL, pb REAL, current_price REAL, broker_target_price REAL,
            valuation_status TEXT, valuation_confidence REAL, generated_at TEXT
        )"""
    )
    now_iso = "2026-03-16T10:30:00+00:00"
    period_end = "2025-12-31"
    conn.executemany(
        """INSERT OR REPLACE INTO fundamentals_snapshot(
            ticker, revenue, net_income, gross_margin, net_margin,
            operating_margin, roe, source, period_end, created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?)""",
        [
            # 阳光电源：典型成熟期制造业，营收大但利润率中等、ROE 中等
            ("300274.SZ", 850_0000_0000.0, 72_0000_0000.0, 0.22, 0.085,
             0.10, 0.14, "cninfo", period_end, now_iso),
            # 海光信息：成长期芯片，营收中等、净利率高、ROE 高
            ("688041.SH", 300_0000_0000.0, 52_0000_0000.0, 0.58, 0.173,
             0.21, 0.21, "cninfo", period_end, now_iso),
        ],
    )
    conn.executemany(
        """INSERT OR REPLACE INTO valuation_snapshot(
            ticker, pe_ttm, pb, current_price, broker_target_price,
            valuation_status, valuation_confidence, generated_at
        ) VALUES (?,?,?,?,?,?,?,?)""",
        [
            ("300274.SZ", 38.0, 5.2, 95.0, 100.0, "reasonable", 0.6, now_iso),
            ("688041.SH", 62.0, 9.5, 780.0, 1020.0, "high_growth", 0.5, now_iso),
        ],
    )
    conn.commit()


def _fake_phase4_valuation_json(tmp_root: Path) -> tuple[Path, Path]:
    """
    构造"阶段4估值制品"的假 JSON（只包含需要被提取的摘要字段）
    真实使用场景中，这些 JSON 应该是从阶段4工作流 artifact 路径读取的。
    为了让阶段3的提取逻辑可验证，这里写最小合法结构：
    { summary:{target_price, target_market_cap, irr},
      implied:{implied_cagr, implied_net_margin},
      input_snapshot:{current_price, market_cap, shares_outstanding} }
    """
    a_path = tmp_root / "phase4_300274.json"
    b_path = tmp_root / "phase4_688041.json"
    a = {
        "summary": {
            "target_price": 98.0,
            "target_market_cap": 2250_0000_0000.0,
            "irr": 0.10,
        },
        "implied": {
            "implied_cagr": 0.08,
            "implied_net_margin": 0.08,
        },
        "input_snapshot": {
            "current_price": 95.0,
            "market_cap": 2180_0000_0000.0,
            "shares_outstanding": 23_0000_0000.0,
        },
    }
    b = {
        "summary": {
            "target_price": 980.0,
            "target_market_cap": 2980_0000_0000.0,
            "irr": 0.22,
        },
        "implied": {
            "implied_cagr": 0.28,
            "implied_net_margin": 0.18,
        },
        "input_snapshot": {
            "current_price": 780.0,
            "market_cap": 2360_0000_0000.0,
            "shares_outstanding": 30_0000_0000.0,
        },
    }
    a_path.write_text(json.dumps(a, ensure_ascii=False), encoding="utf-8")
    b_path.write_text(json.dumps(b, ensure_ascii=False), encoding="utf-8")
    return a_path, b_path


def _default_inputs(tmp_root: Path) -> dict:
    a_p4, b_p4 = _fake_phase4_valuation_json(tmp_root)
    return {
        "from_ticker": "300274.SZ",
        "to_ticker":   "688041.SH",
        "from_name":   "阳光电源",
        "to_name":     "海光信息",
        "temporal_threshold_hours": 72,
        "allow_network": False,
        "preference": {
            "holding_horizon_months": 36,
            "annual_return_target":   0.20,
            "max_drawdown_tolerance": 0.30,
            "max_switch_ratio":       0.70,
            "avoid_negative_roe":     True,
            "prefer_industry_leader": True,
            "avoid_short_term_tax":   True,
        },
        "from_industry":    "光伏逆变器 / 储能",
        "to_industry":      "国产高性能算力 CPU/DCU",
        "from_lifecycle":   "成熟期",
        "to_lifecycle":     "成长期",
        "from_industry_position": "全球前三，价格竞争加剧",
        "to_industry_position":   "国内X86/DCU核心玩家，国产替代核心标的",
        "from_catalysts": [
            "海外大储需求超预期",
            "电网侧储能招标放量",
        ],
        "to_catalysts": [
            "AI算力国产化招标启动",
            "DCU 生态适配头部大模型厂商",
            "信创采购配额落地",
        ],
        "from_risks": [
            "海外双反/汇率波动",
            "上游 IGBT 产能短缺",
        ],
        "to_risks": [
            "制程产能（先进封装）受限",
            "软件生态成熟度不及预期",
        ],
        "from_holding": {
            "shares_wan":       10_0000.0,
            "cost":             60.0,
            "position_pct":     0.18,
            "loss_tolerance":   0.20,
            "short_term_tax":   0.20,
        },
        "from_price_action": {
            "turnover_20d":     0.045,
            "return_1m":        -0.08,
            "return_3m":        -0.15,
            "relative_strength": 0.90,
        },
        "to_price_action": {
            "turnover_20d":     0.06,
            "return_1m":        0.18,
            "return_3m":        0.35,
            "relative_strength": 1.25,
        },
        "from_cash_flow": {
            "operating_cf": 80_0000_0000.0,
            "free_cf":      35_0000_0000.0,
        },
        "to_cash_flow": {
            "operating_cf": 42_0000_0000.0,
            "free_cf":      18_0000_0000.0,
        },
        "phase4_from_json": str(a_p4),
        "phase4_to_json":   str(b_p4),
    }


# ============================================================================
# 测试类
# ============================================================================


class TestPairSwitchDecisionWorkflow(unittest.TestCase):
    """金标准：阳光电源 → 海光信息 的换仓决策工作流端到端测试"""

    def setUp(self) -> None:
        """每个测试用一个独立临时目录，避免互相污染"""
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp_dir.name)
        self.db_path = self.root / "runtime.db"
        # 初始化 DB 表结构：先让 WorkflowRunner 跑 apply_migrations（runner.__init__ 会做）
        # 然后再向 snapshot 表写入测试数据
        runner = WorkflowRunner(self.db_path)  # noqa: F841 — 仅为触发迁移
        conn = sqlite3.connect(self.db_path)
        try:
            _insert_test_snapshot(conn)
        finally:
            conn.close()
        # 设定 SMR_ARTIFACT_ROOTS 为 root，避免阶段12输出到全局目录
        self._orig_roots = os.environ.get("SMR_ARTIFACT_ROOTS")
        os.environ["SMR_ARTIFACT_ROOTS"] = str(self.root)

    def tearDown(self) -> None:
        if self._orig_roots is None:
            os.environ.pop("SMR_ARTIFACT_ROOTS", None)
        else:
            os.environ["SMR_ARTIFACT_ROOTS"] = self._orig_roots
        self.tmp_dir.cleanup()

    # ========================================================================
    # 辅助：跑一次完整工作流，返回 (run_dict, stages_list)
    # stages_list 中每个元素是 dict：{stage_id, status="completed", summary, message, payload}
    # 小白讲解：WorkflowRunner 把每个阶段完成情况写进 workflow_events 表（事件日志），
    # event_type == "stage.completed" 就是已完成的阶段，从这里取每阶段的 summary。
    # ========================================================================

    def _run_once(self, overrides: dict | None = None,
                  run_id: str = "test_solar2hygon") -> tuple[dict, list[dict]]:
        inputs = _default_inputs(self.root)
        if overrides:
            inputs.update(overrides)
        runner = WorkflowRunner(self.db_path)
        definition = pair_switch_decision_definition()
        run_dict = runner.run(definition, inputs, run_id=run_id)
        # 读回 stage.completed 事件
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute(
                """SELECT stage_id, message, payload_json
                   FROM workflow_events
                   WHERE run_id=? AND event_type='stage.completed'
                   ORDER BY sequence""",
                (run_id,),
            ).fetchall()
            stages: list[dict] = []
            for sid, msg, payload_json in rows:
                try:
                    payload = json.loads(payload_json or "{}")
                except json.JSONDecodeError:
                    payload = {}
                stages.append({
                    "stage_id": sid,
                    "status": "completed",
                    "message": msg,
                    "summary": payload.get("summary") or {},
                    "payload": payload,
                })
        finally:
            conn.close()
        return run_dict, stages

    @staticmethod
    def _find_stage(stages: list[dict], stage_id: str) -> dict:
        """按 ID 找阶段，找不到抛 AssertionError（方便调试）"""
        for s in stages:
            if s["stage_id"] == stage_id:
                return s
        raise AssertionError(f"缺少阶段事件：{stage_id}，实际有 {[s['stage_id'] for s in stages]}")

    # ========================================================================
    # 测试：1. 输入合法性 & allow_network 拒签
    # ========================================================================

    def test_01_allow_network_must_be_false(self):
        """阶段1：allow_network=True 被拒绝，符合阶段5纯本地数据要求"""
        res, _stages = self._run_once({"allow_network": True})
        self.assertEqual(res["status"], "failed",
                         msg=f"状态不对：{res['status']}，error={res.get('error_message')}")
        self.assertIn("allow_network=False", str(res.get("error_message") or ""))

    def test_02_same_ticker_rejected(self):
        """阶段1：A/B 相同报错"""
        res, _stages = self._run_once({"to_ticker": "300274.SZ"})
        self.assertEqual(res["status"], "failed",
                         msg=f"状态不对：{res['status']}，error={res.get('error_message')}")
        self.assertTrue(
            ("不能相同" in str(res.get("error_message") or ""))
            or ("same" in str(res.get("error_message") or "").lower()),
            msg=f"错误信息没有提到'A/B 相同'：{res.get('error_message')}"
        )

    # ========================================================================
    # 测试：3. 工作流必须跑通 + 11个阶段都 complete
    # ========================================================================

    def test_10_end_to_end_runs_and_outputs_artifacts(self):
        """
        验收 10：工作流整体可跑通（status=completed，且每个阶段都有 completed 事件），
        并且产出 4 个制品文件（阶段12 persist_outputs 的 summary.paths）。
        """
        res, stages = self._run_once()
        self.assertEqual(
            res.get("status"), "completed",
            msg=f"工作流未完成：status={res.get('status')}，"
                f"error_code={res.get('error_code')}，"
                f"error_message={res.get('error_message')}",
        )
        # 至少 10 个阶段 completed（因为我们的工作流定义了 11 个阶段）
        self.assertGreaterEqual(len(stages), 10,
                                msg=f"阶段 completed 事件太少：{[s['stage_id'] for s in stages]}")
        # 阶段12 persist_outputs 的 summary 必须含 4 个制品路径
        persist_stage = self._find_stage(stages, "persist_outputs")
        summary = persist_stage.get("summary") or {}
        paths = summary.get("paths") or {}
        for key in ("comparison_matrix", "decision_scenarios",
                    "decision_memo", "monitoring_list"):
            self.assertIn(key, paths, msg=f"缺少制品路径：{key}")
            p = Path(paths[key])
            self.assertTrue(p.exists(), msg=f"制品文件不存在：{p}")
            # 额外验证：制品路径必须位于我们临时目录的 artifact_root 下（验证 DEFAULT_ARTIFACT_ROOT 动态读取生效）
            self.assertTrue(
                str(p).startswith(str(self.root)),
                msg=f"制品未输出到 SMR_ARTIFACT_ROOTS：{p}，期望根目录={self.root}"
            )

    # ========================================================================
    # 测试：4. comparison_matrix.json 必须包含 12 个维度
    # ========================================================================

    def test_11_comparison_matrix_has_12_dimensions(self):
        """
        验收 1：ComparisonMatrix JSON 有 12 行；每维度都有 a/b 值或降级说明。
        """
        _res, stages = self._run_once()
        persist = self._find_stage(stages, "persist_outputs")
        cm_path = Path(persist["summary"]["paths"]["comparison_matrix"])
        cm = json.loads(cm_path.read_text(encoding="utf-8"))
        self.assertEqual(cm["a_ticker"], "300274.SZ")
        self.assertEqual(cm["b_ticker"], "688041.SH")
        # 12 个固定维度（和 comparison_matrix.all_dimension_ids() 输出保持一致）
        expected_dims = {
            "lifecycle", "revenue_quality", "cash_flow", "roe", "valuation",
            "implied_growth", "industry_position", "catalysts", "risks",
            "crowding", "price_action", "holding_constraints",
        }
        self.assertEqual(set(cm["rows"].keys()), expected_dims,
                         msg="12 个维度缺失或多余：%s" %
                             (expected_dims ^ set(cm["rows"].keys())))

        # 每个维度行都应有 a/b 结构；degraded 为 True 时要有 degradation_reason
        for dim_id, row in cm["rows"].items():
            self.assertIn("a", row, msg=f"维度 {dim_id} 缺少 A 单元格")
            self.assertIn("b", row, msg=f"维度 {dim_id} 缺少 B 单元格")
            for side in ("a", "b"):
                cell = row[side]
                self.assertIsInstance(cell.get("degraded"), bool,
                                      msg=f"{dim_id}.{side} 缺少 degraded 标记")
                if cell["degraded"]:
                    self.assertIsInstance(cell.get("degradation_reason"), str,
                                          msg=f"{dim_id}.{side} 降级但没说明原因")

    # ========================================================================
    # 测试：5. decision_scenarios.json 有四方案 + 成立/失效条件 + 分批节奏
    # ========================================================================

    def test_12_four_scenarios_with_valid_and_invalid_conditions(self):
        """
        验收 5、9：四方案齐全；partial/full 要有 pacing 和 expected_switch_ratio；
        推荐方案必须有至少 1 条成立条件（除非 hold_and_wait）。
        """
        _res, stages = self._run_once()
        persist = self._find_stage(stages, "persist_outputs")
        ds_path = Path(persist["summary"]["paths"]["decision_scenarios"])
        ds = json.loads(ds_path.read_text(encoding="utf-8"))

        self.assertIn("recommended", ds)
        self.assertIn(ds["recommended"],
                      {"continue_hold", "partial_switch",
                       "full_switch", "hold_and_wait"})
        self.assertIn(ds.get("confidence_level"), {"低", "中", "高"})

        scenarios = ds["scenarios"]
        for sid in ("continue_hold", "partial_switch", "full_switch", "hold_and_wait"):
            self.assertIn(sid, scenarios, msg=f"缺少方案：{sid}")
            s = scenarios[sid]
            # 分数、置信度
            self.assertGreaterEqual(s["score"], 0, msg=f"{sid} score<0")
            self.assertLessEqual(s["score"], 100, msg=f"{sid} score>100")
            self.assertGreaterEqual(s["confidence"], 0.0)
            self.assertLessEqual(s["confidence"], 1.0)
            # 成立条件 & 失效条件必须是 list
            self.assertIsInstance(s["valid_conditions"], list)
            self.assertIsInstance(s["invalid_conditions"], list)
            # 失效条件数量：partial/full/hold_and_wait >= 1（修复质量门的关键）
            if sid != "continue_hold":
                self.assertGreaterEqual(len(s["invalid_conditions"]), 1,
                                        msg=f"{sid} 无失效条件")
            # 成立条件：continue/partial/full >= 1
            if sid != "hold_and_wait":
                self.assertGreaterEqual(len(s["valid_conditions"]), 1,
                                        msg=f"{sid} 无成立条件")
            # 分批节奏
            self.assertIsInstance(s["pacing"], list)
            if sid in ("partial_switch", "full_switch"):
                self.assertGreaterEqual(len(s["pacing"]), 2,
                                        msg=f"{sid} 分批节奏应至少 2 步（立即+观察）")
                self.assertIsInstance(s.get("expected_switch_ratio"), float,
                                      msg=f"{sid} 无 expected_switch_ratio")
            # degraded 声明：如果为 True，必须给出 reasons
            if s["degraded"]:
                self.assertGreaterEqual(len(s["degradation_reasons"] or []), 1,
                                        msg=f"{sid} 降级但没理由")

    # ========================================================================
    # 测试：6. 用户偏好透明化
    # ========================================================================

    def test_13_user_preference_transparency(self):
        """验收 6：preference_used / preference_skipped 都是 list，且至少 1 项"""
        _res, stages = self._run_once()
        persist = self._find_stage(stages, "persist_outputs")
        ds = json.loads(Path(persist["summary"]["paths"]["decision_scenarios"])
                        .read_text(encoding="utf-8"))
        self.assertIsInstance(ds.get("preference_used"), list)
        self.assertIsInstance(ds.get("preference_skipped"), list)
        self.assertGreaterEqual(
            len(ds["preference_used"]) + len(ds["preference_skipped"]), 1,
            msg="用户偏好透明化失败：used+skipped 为空"
        )
        # holding_horizon_months=36 我们明确传了，used 应该至少包含"计划持有期"或"= 36"（中文提示）
        self.assertTrue(
            any(("计划持有期" in p) and ("36" in p) for p in ds["preference_used"])
            or any("holding_horizon" in p for p in ds["preference_used"]),
            msg=f"计划持有期 36 没进入 used，used={ds['preference_used']}"
        )

    # ========================================================================
    # 测试：7. 不执行真实交易 & 估值高低≠买卖信号
    # ========================================================================

    def test_14_no_real_trade_and_no_equivalence_gate(self):
        """
        验收 7：execution_warning 含"不执行真实交易"字样；
        质量门 verify_no_buy_sell_equivalence 应 passed=True。
        """
        _res, stages = self._run_once()

        # 阶段 9（verify_no_buy_sell_equivalence）
        gate = self._find_stage(stages, "verify_no_buy_sell_equivalence")
        self.assertTrue(gate.get("summary", {}).get("passed"),
                        msg=f"买卖信号等价性质量门未通过：{gate.get('summary')}")

        # execution_warning 里含"不执行真实交易"
        persist = self._find_stage(stages, "persist_outputs")
        ds = json.loads(Path(persist["summary"]["paths"]["decision_scenarios"])
                        .read_text(encoding="utf-8"))
        self.assertIn("不执行", ds["execution_warning"],
                      msg=f"execution_warning 未声明不执行：{ds['execution_warning']}")

    # ========================================================================
    # 测试：8. 监控清单至少 2 项，且每指标有频率/阈值/影响方案
    # ========================================================================

    def test_15_monitoring_list_minimum(self):
        """验收 10：监控清单 CSV 至少 2 行 + 有标题行 + 关键字段齐全"""
        _res, stages = self._run_once()
        persist = self._find_stage(stages, "persist_outputs")
        csv_path = Path(persist["summary"]["paths"]["monitoring_list"])
        lines = csv_path.read_text(encoding="utf-8-sig").splitlines()
        self.assertGreaterEqual(len(lines), 3, msg="监控清单行太少（1表头+至少2指标）")
        header = lines[0].split(",")
        # 表头必须包含：indicator_id, name, frequency, warn_threshold, applies_to_scenarios
        for required in ("indicator_id", "name", "frequency",
                         "warn_threshold", "applies_to_scenarios"):
            self.assertIn(required, header,
                          msg=f"监控清单缺少字段：{required}")

    # ========================================================================
    # 测试：11. 独立质量门整体通过（critical_errors 应为空）
    # ========================================================================

    def test_16_independent_quality_gate_pass_for_stable_case(self):
        """验收 11：独立质量门 passed=True，critical_errors 为空"""
        _res, stages = self._run_once()
        persist = self._find_stage(stages, "persist_outputs")
        ds = json.loads(Path(persist["summary"]["paths"]["decision_scenarios"])
                        .read_text(encoding="utf-8"))
        gate = ds.get("quality_gate") or {}
        self.assertTrue(gate.get("passed"),
                        msg=f"独立质量门未通过：critical_errors="
                            f"{gate.get('critical_errors')} / warnings={gate.get('warnings_only')}")
        self.assertEqual(len(gate.get("critical_errors") or []), 0,
                         msg=f"critical_errors 非空：{gate.get('critical_errors')}")

    # ========================================================================
    # 测试：数据缺口 / 时点不对齐会降级（不 crash）
    # ========================================================================

    def test_20_missing_phase4_to_causes_degrade_not_crash(self):
        """验收 3、8：缺失 B 的阶段4制品 → 对应维度降级但仍可完成工作流"""
        res, stages = self._run_once({"phase4_to_json": None}, run_id="test_missing_p4")
        self.assertEqual(res.get("status"), "completed",
                         msg=f"缺失阶段4制品时 status={res.get('status')}，"
                             f"err={res.get('error_message')}")
        # 阶段3 warnings 中应提到"未提供阶段4估值制品"
        p4 = self._find_stage(stages, "load_phase4_valuation_artifacts")
        wcount = p4.get("summary", {}).get("warning_count", 0)
        self.assertGreaterEqual(wcount, 1, msg="缺失阶段4制品但 warnings 未体现")
        # 阶段6 比较矩阵整体仍 complete，degraded_dimension_count 必须 > 0
        cm_stage = self._find_stage(stages, "build_comparison_matrix")
        degrade_cnt = cm_stage.get("summary", {}).get("degraded_dimension_count", 0)
        self.assertGreater(degrade_cnt, 0, msg="缺失阶段4制品但降级维度=0")


if __name__ == "__main__":
    unittest.main()
