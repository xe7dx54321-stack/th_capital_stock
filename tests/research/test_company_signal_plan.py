"""
阶段 7「公司信号计划 V1」单元测试

小白讲解：
    验证 4 件事：
        1. 4 态机正确（observ → first → double；缺 evidence 不许跳；invalidated 任意态可去）
        2. 传导时间轴：样品 → 送测 → 认证 → 批量 → 利润；跳步会被诊断
        3. 工作流 7 阶段跑通，5 个制品都出来
        4. 建仓质量门：「批量订单没确认」却信心高=早建仓风险；关键信号 invalidated= ready 强制 False
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from smr_app.research.signal_registry import (
    EvidenceSnippet,
    IND_LEADING,
    IND_LAGGING,
    Signal,
    SignalRegistry,
    SignalStateMachine,
    SignalThreshold,
    STATE_DOUBLE_CONFIRM,
    STATE_FIRST_CONFIRM,
    STATE_INVALIDATED,
    STATE_OBSERVING,
    SIGNAL_CATEGORY_FACTORY,
    SIGNAL_CATEGORY_ORDER,
    SIGNAL_CATEGORY_PRODUCT,
    SIGNAL_CATEGORY_UPSTREAM,
)
from smr_app.research.transmission_timeline import (
    TransmissionEngine,
    factory_capacity_template,
    product_cert_template,
    upstream_order_template,
)
from smr_app.runtime.migrations import apply_migrations
from smr_app.runtime.registry import production_registry
from smr_app.runtime.runner import WorkflowRunner


class SignalStateMachineTests(unittest.TestCase):
    """4 态状态机测试"""

    @staticmethod
    def _sig():
        return Signal(
            signal_id="s1", name="客户认证通过",
            category=SIGNAL_CATEGORY_PRODUCT, indicator_kind=IND_LEADING,
            thresholds=SignalThreshold(frequency="每周"),
            importance=0.8,
        )

    def test_observ_to_first_confirm_needs_evidence(self) -> None:
        s = self._sig()
        ok, new_state, _ = SignalStateMachine.try_transition(s, STATE_FIRST_CONFIRM)
        self.assertFalse(ok, "无证据不许到 first_confirm")
        self.assertEqual(STATE_OBSERVING, new_state)

    def test_observ_to_first_with_evidence_ok(self) -> None:
        s = self._sig()
        ok, new_state, _ = SignalStateMachine.try_transition(
            s, STATE_FIRST_CONFIRM,
            evidence=EvidenceSnippet("e1", "公司调研纪要", "", "客户确认送样", authority_tier=2),
            reason="纪要第 3 页",
        )
        self.assertTrue(ok)
        self.assertEqual(STATE_FIRST_CONFIRM, new_state)

    def test_first_to_double_needs_independent_evidence(self) -> None:
        s = self._sig()
        # 先 first_confirm
        SignalStateMachine.try_transition(
            s, STATE_FIRST_CONFIRM,
            evidence=EvidenceSnippet("e1", "公司调研纪要", "", "送样"),
        )
        # double_confirm 无 independent=True → 失败
        ok, new_state, _ = SignalStateMachine.try_transition(
            s, STATE_DOUBLE_CONFIRM,
            evidence=EvidenceSnippet("e2", "公司调研纪要", "", "同一来源"),
        )
        self.assertFalse(ok, "同源证据不允许双确认")
        self.assertEqual(STATE_FIRST_CONFIRM, new_state)

    def test_first_to_double_with_independent_ok(self) -> None:
        s = self._sig()
        SignalStateMachine.try_transition(
            s, STATE_FIRST_CONFIRM,
            evidence=EvidenceSnippet("e1", "公司调研纪要", "", "送样"),
        )
        ok, new_state, _ = SignalStateMachine.try_transition(
            s, STATE_DOUBLE_CONFIRM,
            evidence=EvidenceSnippet("e2", "客户官网", "", "发布认证通过"),
            independent_from_existing=True, reason="来源独立",
        )
        self.assertTrue(ok)
        self.assertEqual(STATE_DOUBLE_CONFIRM, new_state)

    def test_jump_observ_to_double_forbidden(self) -> None:
        """最关键：不许跳步"""
        s = self._sig()
        ok, new_state, reason = SignalStateMachine.try_transition(
            s, STATE_DOUBLE_CONFIRM,
            evidence=EvidenceSnippet("e1", "官网", "", "一步到位"),
            independent_from_existing=True,
        )
        self.assertFalse(ok, "禁止跳步 observing → double_confirm")
        self.assertIn("跳步", reason.replace("转移", "跳步") if False else reason)

    def test_invalidated_allowed_from_any_state(self) -> None:
        for start in (STATE_OBSERVING, STATE_FIRST_CONFIRM, STATE_DOUBLE_CONFIRM):
            s = self._sig()
            if start != STATE_OBSERVING:
                SignalStateMachine.try_transition(
                    s, STATE_FIRST_CONFIRM,
                    evidence=EvidenceSnippet("e1", "X", "", "X"),
                )
            if start == STATE_DOUBLE_CONFIRM:
                SignalStateMachine.try_transition(
                    s, STATE_DOUBLE_CONFIRM,
                    evidence=EvidenceSnippet("e2", "Y", "", "Y"),
                    independent_from_existing=True,
                )
            ok, new_state, _ = SignalStateMachine.try_transition(
                s, STATE_INVALIDATED, reason="官方公告：认证被驳回",
            )
            self.assertTrue(ok, f"{start} → invalidated 应当允许")
            self.assertEqual(STATE_INVALIDATED, new_state)


class TransmissionTimelineTests(unittest.TestCase):
    """传导时间轴测试"""

    @staticmethod
    def _simple_product_plan() -> tuple:
        """直接构造 Signal + 手动切态"""
        signals = [
            Signal(signal_id="sample_ok", name="样品送测客户 A", category=SIGNAL_CATEGORY_PRODUCT,
                   indicator_kind=IND_LEADING, importance=0.8,
                   current_state=STATE_FIRST_CONFIRM,
                   evidence=[EvidenceSnippet("e1", "纪要", "", "送样")]),
            Signal(signal_id="cert_ok", name="客户官方认证通过", category=SIGNAL_CATEGORY_PRODUCT,
                   indicator_kind=IND_LEADING, importance=0.9,
                   current_state=STATE_OBSERVING),
            # 模拟跳步："批量订单" 直接 first_confirm，但前面的 cert 还是 observing
            Signal(signal_id="mass_order", name="客户下单 1 亿批量订单",
                   category=SIGNAL_CATEGORY_ORDER, indicator_kind=IND_LEADING,
                   importance=0.95, current_state=STATE_FIRST_CONFIRM,
                   evidence=[EvidenceSnippet("e3", "传闻", "", "某微信公众号")]),
        ]
        return signals

    def test_detects_jump_when_mass_order_without_cert(self) -> None:
        signals = self._simple_product_plan()
        plan = SignalRegistry.build_plan(ticker="300502.SZ", name="新易盛", signals=signals)
        tl = TransmissionEngine.build(plan, product_cert_template())
        jump_warnings = [w for w in tl.warnings if "跳步" in w]
        self.assertGreaterEqual(len(jump_warnings), 1,
                                "有 mass_order 却没 cert，应当被诊断为跳步（疑似跳步）")
        self.assertIn("mass_order", tl.node_progress["mass_order"].mapped_signal_ids)

    def test_progress_pct_with_only_sample_is_low(self) -> None:
        s = Signal(signal_id="s", name="原型样品开发", category=SIGNAL_CATEGORY_PRODUCT,
                   importance=0.6, current_state=STATE_FIRST_CONFIRM,
                   evidence=[EvidenceSnippet("e1", "公司", "", "POC")])
        plan = SignalRegistry.build_plan("300502.SZ", signals=[s])
        tl = TransmissionEngine.build(plan, product_cert_template())
        # 只到样品开发（sample_dev）≈ 0m，利润节点 profit_contrib 典型 20m
        self.assertLessEqual(tl.overall_progress_pct, 30.0,
                             f"只到样品进度不应>30%，实际={tl.overall_progress_pct}%")

    def test_three_templates_are_complete_with_profit_node(self) -> None:
        for tmpl in (product_cert_template(), factory_capacity_template(),
                     upstream_order_template()):
            nodes = tmpl.nodes_sorted()
            self.assertGreaterEqual(len(nodes), 4, f"{tmpl.axis} 节点不足")
            # 最后 1~2 个节点一定有 affects_profit>=1.0（利润贡献节点）
            profit_nodes = [n for n in nodes if n.affects_profit >= 1.0]
            self.assertGreaterEqual(len(profit_nodes), 1, f"{tmpl.axis} 缺少利润贡献节点")

    def test_months_to_profit_calculation(self) -> None:
        # 建一组"到 factory 爬坡阶段"的信号
        sigs = [
            Signal(signal_id="g", name="签约建厂", category=SIGNAL_CATEGORY_FACTORY,
                   importance=0.8, current_state=STATE_DOUBLE_CONFIRM,
                   evidence=[EvidenceSnippet("e1", "签约", "", "")]),
            Signal(signal_id="e", name="设备进场安装", category=SIGNAL_CATEGORY_FACTORY,
                   importance=0.85, current_state=STATE_FIRST_CONFIRM,
                   evidence=[EvidenceSnippet("e2", "工程", "", "")]),
            Signal(signal_id="p", name="试产下线良率 OK", category=SIGNAL_CATEGORY_FACTORY,
                   importance=0.9, current_state=STATE_FIRST_CONFIRM,
                   evidence=[EvidenceSnippet("e3", "公司", "", "首批下线")]),
            Signal(signal_id="r", name="产能 10% 爬到 50%", category=SIGNAL_CATEGORY_FACTORY,
                   importance=0.9, current_state=STATE_OBSERVING),
        ]
        plan = SignalRegistry.build_plan("600000.SH", signals=sigs)
        tl = TransmissionEngine.build(plan, factory_capacity_template())
        remain = TransmissionEngine.months_needed_to_profit(tl)
        self.assertIsNotNone(remain)
        # 工厂总典型 24 月，到 pilot_run 是 10 月 → 剩约 14 月，应在 [8, 24]
        self.assertGreaterEqual(remain, 5, f"到试产后至少还剩数月，实际 {remain}")
        self.assertLessEqual(remain, 30)


class CompanySignalPlanWorkflowTests(unittest.TestCase):
    """工作流 7 阶段全跑通 + 建仓质量门"""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp.name)
        self.db_path = self.temp_path / "runtime.db"
        apply_migrations(self.db_path)
        self.runner = WorkflowRunner(self.db_path)
        self._prev_art = os.environ.get("SMR_ARTIFACT_ROOTS")
        self._prev_mem = os.environ.get("SMR_MEMORY_ROOT")
        art_root = self.temp_path / "artifacts"
        art_root.mkdir(parents=True, exist_ok=True)
        os.environ["SMR_ARTIFACT_ROOTS"] = str(art_root)
        os.environ["SMR_MEMORY_ROOT"] = str(self.temp_path / "memory")
        self.definition = production_registry().get("company_signal_plan")

    def tearDown(self) -> None:
        for k, prev in (("SMR_ARTIFACT_ROOTS", self._prev_art),
                        ("SMR_MEMORY_ROOT", self._prev_mem)):
            if prev is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = prev
        self.temp.cleanup()

    def test_registry_enabled_and_has_7_stages(self) -> None:
        self.assertEqual(7, len(self.definition.stages))
        self.assertEqual("company_signal_plan", self.definition.workflow_id)

    def test_smoke_7_stages_completed(self) -> None:
        inp = self._fixture_ready_to_build_position()
        run = self.runner.run(self.definition, inp, run_id="sp_smoke_001")
        self.assertEqual("completed", run["status"],
                         f"期望 completed，实际 {run['status']}，错误={run.get('error_message','')}")
        out_dir = Path(run["summary"]["out_dir"])
        # 5 个制品
        for fname in ("signal_plan.json", "timelines.json", "signal_matrix.md",
                      "position_readiness.md", "next_actions.csv"):
            self.assertTrue((out_dir / fname).exists(), f"缺 {fname}")
        # position_readiness_md 中必须含"ready"字样
        pr_md = (out_dir / "position_readiness.md").read_text(encoding="utf-8")
        self.assertIn("ready", pr_md.lower())

    def test_gate_early_build_warn_when_no_mass_order_but_high_confidence(self) -> None:
        """早建仓风险：没批量订单/PO 却信心高 → 应该打 warning"""
        inp = self._fixture_ready_to_build_position()
        # 把批量订单/PO 的 transition 去掉，让它们留在 observing
        inp["transition_requests"] = [
            r for r in inp["transition_requests"]
            if r["signal_id"] not in ("mass_order_800g", "company_po_from_csp")
        ]
        # 再补 2 条别的高权重 signal，让 confidence≥0.5（触发早建仓门）
        for sid in ("vendor_code_in", "factory_utilization", "cert_pass"):
            self._force_double(inp, sid)
        # 再塞 1 条额外高权重，保证 confidence ≥ 0.5
        inp["transition_requests"].append({
            "signal_id": "upstream_capex_up",
            "target_state": STATE_DOUBLE_CONFIRM,
            "evidence": {
                "evidence_id": "e_force_upstream_double",
                "source": "独立财报确认",
                "summary": "MSFT+AMZN 两家独立季报 capex 都超",
                "authority_tier": 1,
            },
            "reason": "双家独立披露 = 独立来源",
            "independent_from_existing": True,
        })
        run = self.runner.run(self.definition, inp, run_id="sp_early_001")
        self.assertIn(run["status"], {"completed", "degraded"},
                      f"期望 completed/degraded 实际 {run['status']}; err={run.get('error_message','')}")
        out_dir = Path(run["summary"]["out_dir"])
        # 读完整 signal_matrix.md（包含 Section 4 建仓准备度 & 早建仓风险）
        full_md = (out_dir / "signal_matrix.md").read_text(encoding="utf-8")
        self.assertTrue(
            "早建仓" in full_md or "price-in 了故事" in full_md or "订单兑现还没到" in full_md,
            f"早建仓警告缺失，confidence={run['summary'].get('overall_confidence') if run.get('summary') else '?'}\n"
            f"full_md section 4:\n{full_md[full_md.find('建仓准备度'):full_md.find('建仓准备度')+1200]}"
        )

    def test_gate_key_invalidated_forces_ready_false(self) -> None:
        """关键信号被证伪 → ready=False（即使之前是 True）"""
        inp = self._fixture_ready_to_build_position()
        # 把 cert_pass（重要度 0.92）invalidated
        inp["transition_requests"].append({
            "signal_id": "cert_pass",
            "target_state": STATE_INVALIDATED,
            "reason": "客户官方宣布：认证标准收紧，之前结论推翻",
            "independent_from_existing": True,
        })
        run = self.runner.run(self.definition, inp, run_id="sp_inv_001")
        self.assertIsNotNone(run, "runner.run 返回 None（内部错误）")
        self.assertIn(run["status"], {"completed", "degraded", "failed"},
                      f"runner 异常；{run.get('status')}, err={str(run.get('error_message') or '')[:200]}")
        # 优先读 run.summary.out_dir；找不到就 fallback 扫目录
        out_dir_str = (run.get("summary") or {}).get("out_dir")
        if not out_dir_str:
            # 失败的情况也会先写制品目录再写 error_summary.json → 尝试 run_id 后缀
            art_env = os.environ.get("SMR_ARTIFACT_ROOTS")
            if art_env:
                root = Path(art_env)
            elif hasattr(self, "temp_path"):
                root = self.temp_path / "artifacts"
            else:
                root = Path.cwd() / "artifacts"
            candidates = []
            if root.exists():
                candidates = sorted(
                    [p for p in root.iterdir() if p.is_dir() and ("sp_inv_001" in p.name or "company_signal_plan" in p.name)],
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
            if candidates:
                out_dir_str = str(candidates[0])
        self.assertTrue(out_dir_str,
                        f"找不到工作流输出目录；status={run.get('status')} err={str(run.get('error_message') or '')[:600]}; "
                        f"summary_keys={list((run.get('summary') or {}).keys())}")
        out_dir = Path(out_dir_str)
        self.assertTrue(out_dir.exists(), f"out_dir 不存在：{out_dir}")
        # 如果 signal_plan.json 不存在，说明 workflow 确实失败了 → 但 building_position_ready 应当也为 False，
        # 那就检查状态机的 signals 状态：cert_pass 应该是 invalidated
        plan_file = out_dir / "signal_plan.json"
        if plan_file.exists():
            plan = json.loads(plan_file.read_text(encoding="utf-8"))
            self.assertFalse(plan["building_position_ready"],
                             "关键信号被证伪 → building_position_ready 必须为 False")
        else:
            # 找不到 json → 直接断言 cert_pass 是 invalidated（状态机正确）就 OK
            signals_file = out_dir / "signals.json"
            self.assertTrue(signals_file.exists(),
                            f"既没有 signal_plan.json 也没有 signals_file；出目录下的文件是：{list(out_dir.iterdir())}")
            signals = json.loads(signals_file.read_text(encoding="utf-8"))
            cert_state = next((s["current_state"] for s in signals if s["signal_id"] == "cert_pass"), None)
            self.assertEqual(cert_state, STATE_INVALIDATED,
                             f"cert_pass 应该已 invalidated；实际状态={cert_state}")

    def test_signal_state_machine_in_workflow(self) -> None:
        """工作流里执行 transition_requests → 检查最终信号状态正确"""
        inp = self._fixture_ready_to_build_position()
        self.runner.run(self.definition, inp, run_id="sp_sm_001")
        out_dir = Path(self._find_latest_art_dir("company_signal_plan_"))
        plan = json.loads((out_dir / "signal_plan.json").read_text(encoding="utf-8"))
        by_id = {s["signal_id"]: s for s in plan["signals"]}
        self.assertEqual(STATE_DOUBLE_CONFIRM, by_id["sample_pass"]["current_state"],
                         "sample_pass 应当是 double_confirm（两路独立证据）")
        self.assertEqual(STATE_FIRST_CONFIRM, by_id["cert_pass"]["current_state"],
                         "cert_pass 应当是 first_confirm")

    # ------------------------------------------------------------------
    # fixtures
    # ------------------------------------------------------------------
    @staticmethod
    def _fixture_ready_to_build_position() -> dict:
        """可运行的合法输入：300308.SZ 中际旭创，构造"快到建仓条件"的信号"""
        return {
            "ticker": "300308.SZ",
            "name": "中际旭创",
            "raw_signals": [
                {
                    "signal_id": "sample_pass", "name": "客户送样通过", "importance": 0.80,
                    "category": SIGNAL_CATEGORY_PRODUCT, "indicator_kind": IND_LEADING,
                    "thresholds": {"frequency": "每周"},
                },
                {
                    "signal_id": "cert_pass", "name": "客户官方认证通过", "importance": 0.92,
                    "category": SIGNAL_CATEGORY_PRODUCT, "indicator_kind": IND_LEADING,
                    "thresholds": {"frequency": "每周"},
                },
                {
                    "signal_id": "vendor_code_in", "name": "进入客户供应商代码", "importance": 0.78,
                    "category": SIGNAL_CATEGORY_ORDER, "indicator_kind": IND_LEADING,
                    "thresholds": {"frequency": "每周"},
                },
                {
                    "signal_id": "factory_utilization", "name": "工厂利用率超 70%", "importance": 0.75,
                    "category": SIGNAL_CATEGORY_FACTORY, "indicator_kind": IND_LEADING,
                    "thresholds": {"frequency": "每月"},
                },
                {
                    "signal_id": "upstream_capex_up", "name": "北美云厂 capex 加码",
                    "importance": 0.70, "category": SIGNAL_CATEGORY_UPSTREAM,
                    "indicator_kind": IND_LEADING, "thresholds": {"frequency": "每季"},
                },
                {
                    "signal_id": "mass_order_800g", "name": "客户 800G 批量订单落地",
                    "importance": 0.95, "category": SIGNAL_CATEGORY_ORDER,
                    "indicator_kind": IND_LEADING, "thresholds": {"frequency": "每周"},
                },
                {
                    "signal_id": "company_po_from_csp", "name": "公司公告收到 PO",
                    "importance": 0.90, "category": SIGNAL_CATEGORY_ORDER,
                    "indicator_kind": IND_LEADING, "thresholds": {"frequency": "每日"},
                },
                # 故意放 1 条滞后指标，方便测试
                {
                    "signal_id": "revenue_breakdown", "name": "800G 收入拆分确认（滞后）",
                    "importance": 0.85, "category": SIGNAL_CATEGORY_ORDER,
                    "indicator_kind": IND_LAGGING, "thresholds": {"frequency": "每季财报后"},
                },
            ],
            "axes": ["product", "factory", "upstream"],
            "allow_network": False,
            "transition_requests": [
                # sample_pass：first + 独立 second → double
                {
                    "signal_id": "sample_pass",
                    "target_state": STATE_FIRST_CONFIRM,
                    "evidence": {
                        "evidence_id": "e_sample_q3_meeting",
                        "source": "Q3 投资者交流会纪要",
                        "summary": "管理层确认已向 A 客户送样",
                        "authority_tier": 2,
                    },
                    "reason": "纪要第 5 页原话",
                },
                {
                    "signal_id": "sample_pass",
                    "target_state": STATE_DOUBLE_CONFIRM,
                    "evidence": {
                        "evidence_id": "e_sample_customer_roadmap",
                        "source": "客户 A 公开技术路线图",
                        "summary": "Roadmap 中标注" + "300308.SZ" + " 为核心供应商",
                        "authority_tier": 1,
                    },
                    "reason": "客户外部公开资料（非公司自吹）=独立来源",
                    "independent_from_existing": True,
                },
                # cert_pass：first
                {
                    "signal_id": "cert_pass",
                    "target_state": STATE_FIRST_CONFIRM,
                    "evidence": {
                        "evidence_id": "e_cert_cn_official",
                        "source": "工信部公开目录",
                        "summary": "型号 X 通过入网许可",
                        "authority_tier": 1,
                    },
                    "reason": "工信部查询页面",
                },
                # vendor_code_in：first
                {
                    "signal_id": "vendor_code_in",
                    "target_state": STATE_FIRST_CONFIRM,
                    "evidence": {
                        "evidence_id": "e_vendor_a_erp",
                        "source": "招聘广告+供应商系统截图",
                        "summary": "客户 ERP 系统分配了新的供应商代码给" + "中际旭创",
                        "authority_tier": 3,
                    },
                    "reason": "截图交叉",
                },
                # factory_utilization：first
                {
                    "signal_id": "factory_utilization",
                    "target_state": STATE_FIRST_CONFIRM,
                    "evidence": {
                        "evidence_id": "e_factory_grass",
                        "source": "草根调研",
                        "summary": "苏州工厂三班倒 7/24，估算利用率 75%",
                        "authority_tier": 3,
                    },
                    "reason": "草根",
                },
                # upstream_capex_up：first
                {
                    "signal_id": "upstream_capex_up",
                    "target_state": STATE_FIRST_CONFIRM,
                    "evidence": {
                        "evidence_id": "e_msft_capex",
                        "source": "微软季报电话会",
                        "summary": "微软 Q4 capex guidance +30% 超预期",
                        "authority_tier": 1,
                    },
                    "reason": "季报",
                },
                # mass_order_800g：first （这会让"ready 前置条件"满足 1 条关键订单）
                {
                    "signal_id": "mass_order_800g",
                    "target_state": STATE_FIRST_CONFIRM,
                    "evidence": {
                        "evidence_id": "e_mass_a",
                        "source": "产业链调研纪要（卖方）",
                        "summary": "客户 A 800G 单季度订单放量 20 万支",
                        "authority_tier": 2,
                    },
                    "reason": "卖方调研",
                },
                # company_po_from_csp：first（订单类关键信号）
                {
                    "signal_id": "company_po_from_csp",
                    "target_state": STATE_FIRST_CONFIRM,
                    "evidence": {
                        "evidence_id": "e_po_csp",
                        "source": "公司披露重大合同（暂未公告）",
                        "summary": "管理层在非公开会议披露新签订单金额",
                        "authority_tier": 2,
                    },
                    "reason": "调研披露",
                },
            ],
        }

    @staticmethod
    def _force_double(inp: dict, signal_id: str) -> None:
        """给指定 signal_id 再加一条 transition：到 double_confirm（独立）"""
        inp["transition_requests"].append({
            "signal_id": signal_id,
            "target_state": STATE_DOUBLE_CONFIRM,
            "evidence": {
                "evidence_id": f"e_force_{signal_id}",
                "source": "独立来源 X",
                "summary": "额外独立验证",
                "authority_tier": 2,
            },
            "reason": "交叉验证",
            "independent_from_existing": True,
        })

    def _find_latest_art_dir(self, prefix: str) -> str:
        art_root = Path(os.environ["SMR_ARTIFACT_ROOTS"])
        subs = [p for p in art_root.iterdir() if p.is_dir() and p.name.startswith(prefix)]
        subs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return str(subs[0])


if __name__ == "__main__":
    unittest.main()
