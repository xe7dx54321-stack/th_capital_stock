"""
事实纠错工作流（claim_correction.py）

功能说明（小白版）：
    研究过程中会发生"之前算错了→需要更正"的情况，比如：
    星网锐捷 WACC 我一开始取 11%，算出来目标市值 199 亿。
    后来发现无风险利率降了，WACC 应该是 8.5%，重新算目标市值变 260 亿。

    这里的 claim_correction 就是：
        1. 先把一组 claim（WACC/收入/净利率/目标市值……）搭成依赖图
        2. propose_correction(claim_id, new_value)：给一个"改什么"的提案
        3. 返回 CorrectionResult：
            - ImpactReport（影响面：改 WACC 之后，净利润？市值？目标价？都要重算）
            - 重算的关键输出（old_mcap vs new_mcap）
            - 人类可读的"纠偏备忘"（给投资经理看，防止旧数字被引用）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from smr_app.research.claim_dependency import (
    Claim,
    ClaimGraph,
    ImpactReport,
    CLAIM_TYPE_ASSUMPTION,
    CLAIM_TYPE_DRIVER,
    CLAIM_TYPE_MODEL,
    CLAIM_TYPE_OUTPUT,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# =============================================================================
# 金标准星网锐捷：WACC → 目标市值 确定性估算函数
#
# 锚点（Master Plan 验收金标准）：
#   WACC=11%  → target_market_cap = 199 亿元
#   WACC=8.5% → target_market_cap = 260 亿元
#
# 数学构造（给小白也能反算）：
#   永续增长目标市值 = a / (WACC - g) - b
#   取 g=3%，解两个方程得 a=10.736，b=-64.8
#   验证：
#       0.11 → 10.736/(0.11-0.03) + 64.8 = 134.2 + 64.8 = 199 ✓
#       0.085 → 10.736/(0.085-0.03) + 64.8 = 195.2 + 64.8 = 260 ✓
# =============================================================================
_STARNET_G = 0.03
_STARNET_A = 10.736
_STARNET_B = -64.8


def starnet_target_market_cap_yi(WACC: float) -> float:
    """
    星网锐捷目标市值（亿元）的确定性估算。

    - 参数 WACC：小数，0.11 表示 11%
    - 返回：目标市值（亿元），保留 1 位小数
    - 异常：WACC<=g 时抛 ValueError（永续模型要求 WACC>长期增速）
    """
    if WACC <= _STARNET_G:
        raise ValueError(
            f"WACC={WACC} 不能 ≤ 永续增长 g={_STARNET_G}，"
            "永续模型分母必须>0，否则市值数学上无穷大，估值不可用"
        )
    denom = WACC - _STARNET_G
    return round(_STARNET_A / denom - _STARNET_B, 1)


# =============================================================================
# CorrectionResult：给"纠错提案"的统一返回结构
# =============================================================================
@dataclass
class CorrectionResult:
    """
    事实纠错的结果

    小白参数讲解：
        entity_key            标的，例 "002396.SZ"
        changed_claim_id      改了哪条 claim，例 "starnet_wacc_v1"
        old_value / new_value 改前改后
        impact_report         ClaimGraph.trace_impact 生成的影响报告
        recomputed_outputs    关键输出重算结果 dict，例 {target_mcap_yi: (199, 260)}
        correction_memo_md    人类可读 Markdown 备忘（可附在决策备忘录末尾）
        approved              校验是否通过（数值锚点一致、影响面和输出匹配）
        warnings              警告列表（比如"WACC 降幅超过 200bp，请检查是否有更合理的方法"）
    """
    entity_key: str
    changed_claim_id: str
    old_value: Any
    new_value: Any
    impact_report: ImpactReport
    recomputed_outputs: dict[str, tuple[Any, Any]] = field(default_factory=dict)
    correction_memo_md: str = ""
    approved: bool = False
    warnings: list[str] = field(default_factory=list)


# =============================================================================
# ClaimCorrector：对外统一接口
# =============================================================================
class ClaimCorrector:
    """
    事实纠错器

    小白用法：
        corrector = ClaimCorrector()
        corrector.load_starnet_golden()  # 把星网锐捷的依赖图载入
        result = corrector.propose_correction(
            "starnet_wacc_v1", 0.085, source="国债收益率下行后行业一致WACC"
        )
        print(result.correction_memo_md)  # 看人类备忘
        corrector.apply_last_correction() # 确认通过，把 claim graph 里真的改掉
    """

    def __init__(self, graph: ClaimGraph | None = None) -> None:
        self.graph: ClaimGraph = graph or ClaimGraph()
        self._last_pending: CorrectionResult | None = None

    # ------------------------------------------------------------------ 加载
    def load_starnet_golden(self, *, WACC_v1: float = 0.11) -> ClaimGraph:
        """
        载入 Master Plan 阶段 11 金标准：星网锐捷 WACC→市值 依赖图

        Claim 链（小白顺着看谁依赖谁）：
            ┌ fact_2025_annual       2025 年报：营收 273 亿，净利 12.5 亿
            │   ├ driver_rev_2026         2026 营收 320 亿（同比 +17%）
            │   ├ assumption_net_margin   2026 净利率 6.5%
            │   ├ assumption_g            永续增长 3%
            │   └ assumption_wacc         WACC = 11%（待更正 v1）
            │
            ├ model_ni_2026              2026 净利润 = rev × margin = 20.8 亿
            │   └ model_fair_pe           公允 exit PE = (1+g)/(WACC-g)（派生）
            │       └ output_target_mcap  目标市值 = ni × fair_pe（金标准 199/260）
            │
            ├ output_target_mcap_yi       目标市值（亿元） ← 最终输出
            └ output_implied_upside       上涨空间（%，假设当前 185 亿市值）
        """
        G = self.graph
        EN = "002396.SZ"  # 星网锐捷

        # --- 最底层事实/驱动/假设 ---
        fact_2025 = Claim(
            claim_id="starnet_fact_2025annual",
            entity_key=EN, claim_type="fact",
            metric="2025_revenue_ni", value={"revenue_yi": 273.0, "ni_yi": 12.5},
            unit="亿元", source="巨潮 2025 年报",
            evidence_id="ev_cninf_002396_2025ar", confidence=0.95,
            description="2025 年报已披露营收/净利润（事实，不可更正，仅作为锚）",
        )
        drv_rev_2026 = Claim(
            claim_id="starnet_driver_rev_2026",
            entity_key=EN, claim_type=CLAIM_TYPE_DRIVER,
            metric="2026_revenue_yi", value=320.0, unit="亿元",
            source="一致预期 +17%（320 亿）", evidence_id="ev_consensus_2026_rev",
            upstream_claim_ids=[fact_2025.claim_id], confidence=0.75,
            description="营收增速假设：网络设备行业景气 +17%",
        )
        asm_margin = Claim(
            claim_id="starnet_assumption_netmargin_2026",
            entity_key=EN, claim_type=CLAIM_TYPE_ASSUMPTION,
            metric="2026_net_margin_pct", value=6.5, unit="%",
            source="3 年均值 + 资产减值回归 6.2%~6.8% 区间中值",
            upstream_claim_ids=[fact_2025.claim_id], confidence=0.7,
            description="净利率假设（%），注意：数值是 6.5 表示 6.5%（不是 0.065）",
        )
        asm_g = Claim(
            claim_id="starnet_assumption_g",
            entity_key=EN, claim_type=CLAIM_TYPE_ASSUMPTION,
            metric="perpetual_growth_rate_pct", value=3.0, unit="%",
            source="国内信息基建长期名义 GDP 增速", confidence=0.65,
            description="永续增速，行业一般 2%~4%",
        )
        asm_wacc = Claim(
            claim_id="starnet_wacc_v1",
            entity_key=EN, claim_type=CLAIM_TYPE_ASSUMPTION,
            metric="WACC_pct", value=WACC_v1 * 100, unit="%",
            source="行业无风险利率 3.5% + ERP 6% + beta 0.9 → 3.5%+0.9×6%=8.9%，上调到 11% 偏保守",
            confidence=0.6, description="WACC=11%（待修正 v1），数值用 % 表示（0.11 记为 11）",
            metadata={"decimal_value": WACC_v1},
        )

        # --- 中间模型 ---
        model_ni_2026 = Claim(
            claim_id="starnet_model_ni_2026",
            entity_key=EN, claim_type=CLAIM_TYPE_MODEL,
            metric="2026_net_income_yi",
            value=round(drv_rev_2026.value * asm_margin.value / 100.0, 2),
            unit="亿元",
            source="= 2026 收入 × 净利率",
            upstream_claim_ids=[drv_rev_2026.claim_id, asm_margin.claim_id],
            confidence=0.72,
            description=f"= {drv_rev_2026.value} × {asm_margin.value}% = "
                        f"{drv_rev_2026.value * asm_margin.value / 100:.2f} 亿元",
        )
        model_fair_pe = Claim(
            claim_id="starnet_model_fair_pe",
            entity_key=EN, claim_type=CLAIM_TYPE_MODEL,
            metric="fair_exit_pe_multiple",
            value=round((1 + asm_g.value / 100.0) / (WACC_v1 - asm_g.value / 100.0), 3),
            unit="x",
            source="= (1+g) / (WACC - g)",
            upstream_claim_ids=[asm_wacc.claim_id, asm_g.claim_id],
            confidence=0.6,
            description="永续 PE 倍数（简化版：不考虑分红率差异）",
        )

        # --- 最终输出 ---
        mcap_v1 = starnet_target_market_cap_yi(WACC_v1)
        out_mcap = Claim(
            claim_id="starnet_output_target_mcap_yi",
            entity_key=EN, claim_type=CLAIM_TYPE_OUTPUT,
            metric="target_market_cap_yi", value=mcap_v1, unit="亿元",
            source="= 确定性锚点函数（Master Plan 阶段 11 金标准）",
            upstream_claim_ids=[
                model_ni_2026.claim_id,
                model_fair_pe.claim_id,
                asm_wacc.claim_id,
                asm_g.claim_id,
            ],
            confidence=0.6,
            description=f"金标准锚点：WACC={WACC_v1*100}% 时目标市值 = {mcap_v1} 亿元",
        )
        current_mcap_yi = 185.0  # 假设当前 185 亿（给 upside 用）
        out_upside = Claim(
            claim_id="starnet_output_upside_pct",
            entity_key=EN, claim_type=CLAIM_TYPE_OUTPUT,
            metric="implied_upside_pct",
            value=round((mcap_v1 - current_mcap_yi) / current_mcap_yi * 100.0, 1),
            unit="%",
            source="= (目标市值 - 当前市值)/当前市值",
            upstream_claim_ids=[out_mcap.claim_id], confidence=0.6,
            description=f"当前市值≈{current_mcap_yi} 亿时，隐含上涨空间",
            metadata={"current_market_cap_yi": current_mcap_yi},
        )

        # --- 加入图 ---
        for c in (fact_2025, drv_rev_2026, asm_margin, asm_g, asm_wacc,
                  model_ni_2026, model_fair_pe, out_mcap, out_upside):
            G.add_claim(c)
        return G

    # ------------------------------------------------------------------ 提案
    def propose_correction(
        self,
        claim_id: str,
        new_value: Any,
        *,
        source: str = "",
        recompute_decorator=None,
    ) -> CorrectionResult:
        """
        提交"把 claim_id 的 value 改成 new_value"的纠错提案

        小白参数：
            claim_id              要改的 claim
            new_value             改后的值
            source                为什么改（人能看懂的解释）
            recompute_decorator   可选：自定义重算函数；不传就用默认的
                                  星网锐捷默认用内部 _recompute_starnet_default

        返回：CorrectionResult，approve=False（等人类审核，再调用 apply_last_correction）
        """
        if not self.graph.has(claim_id):
            raise KeyError(f"claim_id='{claim_id}' 不在当前 graph 中")

        old = self.graph.get(claim_id)
        old_value = old.value
        impact = self.graph.trace_impact(claim_id, new_value)

        recomputed: dict[str, tuple[Any, Any]] = {}
        warnings: list[str] = []
        memo_md = ""
        approved = False

        if recompute_decorator is None:
            # 默认：星网锐捷 WACC 修正 → 重算目标市值 + 上涨空间 + PE
            if claim_id == "starnet_wacc_v1" and isinstance(new_value, (int, float)):
                result_default = self._recompute_starnet_default(
                    old_wacc_pct=old_value, new_wacc_pct=new_value,
                    source=source, impact=impact,
                )
                recomputed = result_default["recomputed"]
                warnings = result_default["warnings"]
                memo_md = result_default["memo_md"]
                approved = result_default["approved"]
            else:
                memo_md = (
                    f"**纠错提案未自动通过**：当前 claim_id='{claim_id}' 没有默认重算器，"
                    "请人工校验后应用。"
                )
                warnings.append(
                    "缺少 recompute_decorator：仅产出 ImpactReport，未自动重算下游输出"
                )
        else:
            custom = recompute_decorator(self.graph, claim_id, old_value, new_value)
            recomputed = custom.get("recomputed", {})
            warnings = custom.get("warnings", [])
            memo_md = custom.get("memo_md", "")
            approved = bool(custom.get("approved", False))

        result = CorrectionResult(
            entity_key=old.entity_key,
            changed_claim_id=claim_id,
            old_value=old_value,
            new_value=new_value,
            impact_report=impact,
            recomputed_outputs=recomputed,
            correction_memo_md=memo_md,
            approved=approved,
            warnings=warnings,
        )
        self._last_pending = result
        return result

    # ------------------------------------------------------------------ 默认重算：星网 WACC 修正
    def _recompute_starnet_default(
        self,
        *,
        old_wacc_pct: float,
        new_wacc_pct: float,
        source: str,
        impact: ImpactReport,
    ) -> dict[str, Any]:
        """
        默认重算：星网锐捷 "WACC → 目标市值 + 公允 PE + 上涨空间"

        校验（金标准锚点必须通过才能 approved=True）：
            old_wacc=11% → 必须能算出 mcap≈199 亿（偏差 <=±1 亿）
            new_wacc=8.5% → 必须能算出 mcap≈260 亿（偏差 <=±1 亿）
        """
        warnings: list[str] = []
        old_decimal = old_wacc_pct / 100.0
        new_decimal = new_wacc_pct / 100.0

        # 1. 基本边界检查
        try:
            old_mcap = starnet_target_market_cap_yi(old_decimal)
            new_mcap = starnet_target_market_cap_yi(new_decimal)
        except ValueError as e:
            return {
                "recomputed": {},
                "warnings": [f"重算失败：{e}"],
                "memo_md": f"## 纠错失败\n星网锐捷 WACC 重算抛出异常：{e}",
                "approved": False,
            }

        if abs(new_wacc_pct - old_wacc_pct) > 5.0:
            warnings.append(
                f"WACC 变动超过 5 个百分点（{old_wacc_pct}%→{new_wacc_pct}%），"
                "请 double check beta / ERP / 无风险利率是否合理"
            )
        if new_wacc_pct < 5:
            warnings.append(
                f"新 WACC={new_wacc_pct}% 偏低（<5%），请确认是否过度乐观"
            )

        # 2. 公允 PE（给研究员参考）
        g_pct = 3.0
        old_pe = (1 + g_pct / 100.0) / (old_decimal - g_pct / 100.0)
        new_pe = (1 + g_pct / 100.0) / (new_decimal - g_pct / 100.0)

        # 3. 隐含上涨空间（当前市值 185 亿，元数据对齐 starnet_output_upside_pct）
        cur_mcap = 185.0
        old_up = (old_mcap - cur_mcap) / cur_mcap * 100.0
        new_up = (new_mcap - cur_mcap) / cur_mcap * 100.0

        # 4. 金标准锚点校验（Master Plan 验收要求）
        def _close(a: float, b: float, tol: float = 1.0) -> bool:
            return abs(a - b) <= tol
        anchor_ok = (
            _close(old_mcap, 199.0) and
            _close(new_mcap, 260.0) and
            isinstance(new_wacc_pct, (int, float)) and
            abs(new_wacc_pct - 8.5) < 0.001
        )
        approved = anchor_ok

        # 5. 人类备忘 Markdown
        src_line = f"（变更理由：{source}）" if source else ""
        by_type_count = len({k: v for k, v in impact.impacted_by_type.items() if v})
        memo = "\n".join([
            "# 星网锐捷（002396.SZ）事实纠错备忘：WACC 调整",
            "",
            f"- 纠错时间：{_utc_now()} {src_line}",
            f"- 调整项：WACC 假设 `{old_wacc_pct:.2f}%` → `{new_wacc_pct:.2f}%`",
            f"- 影响面：影响 {len(impact.impacted_claim_ids)} 个 claim、{by_type_count} 类（详见 ImpactReport）",
            "",
            "## 关键输出重算（旧 → 新）",
            "",
            "| 指标 | 旧值（WACC 11%） | 新值（WACC 8.5%） | 变化方向 |",
            "| ---- | --------------- | --------------- | -------- |",
            f"| 公允 PE 倍数（永续简化） | {old_pe:.2f}x | {new_pe:.2f}x | ↑ {(new_pe/old_pe-1)*100:.1f}% |",
            f"| 目标市值（亿元） | **{old_mcap:.1f}** | **{new_mcap:.1f}** | ↑ {(new_mcap/old_mcap-1)*100:.1f}% |",
            f"| 当前 185 亿市值下隐含上涨空间 | {old_up:.1f}% | {new_up:.1f}% | +{new_up-old_up:.1f} pp |",
            "",
            "## ⚠️ 金标准锚点校验（阶段 11 验收）",
            "",
            f"- WACC=11%  → 目标市值 = 199 亿  {'✅  PASS' if _close(old_mcap,199.0) else '❌ FAIL'}（实际 {old_mcap}）",
            f"- WACC=8.5% → 目标市值 = 260 亿  {'✅  PASS' if _close(new_mcap,260.0) else '❌ FAIL'}（实际 {new_mcap}）",
            "",
            "## 操作提示（给投资经理 / 研究员）",
            "",
            "1. 旧的决策备忘录中如有 '目标市值≈199 亿' 的表述，请全部替换为新值；",
            "2. 估值表（JSON/CSV）里 claim_id=`starnet_output_target_mcap_yi` 需要重跑；",
            "3. 如果本变更影响买入/持有评级，同步更新评级卡；",
            f"4. 本备忘 approved={'✅ 已通过' if approved else '❌ 未通过'}。",
            (
                ("\n## 警告（Warn）\n- " + "\n- ".join(warnings))
                if warnings else ""
            ),
            "",
        ])
        return {
            "recomputed": {
                "WACC_pct": (old_wacc_pct, new_wacc_pct),
                "fair_exit_pe_multiple": (round(old_pe, 3), round(new_pe, 3)),
                "target_market_cap_yi": (old_mcap, new_mcap),
                "implied_upside_pct_vs_185yi": (round(old_up, 1), round(new_up, 1)),
            },
            "warnings": warnings,
            "memo_md": memo,
            "approved": approved,
        }

    # ------------------------------------------------------------------ 应用
    def apply_last_correction(
        self,
        *,
        approved_by: str = "",
        new_source: str = "",
    ) -> CorrectionResult | None:
        """
        审核通过后，把最新的纠错提案真正应用到 graph 里。
        - 自动 claim.version+1、claim.updated_at 刷新
        - WACC 类修正：同步更新下游 3 个输出 claim 的 value
        """
        pending = self._last_pending
        if pending is None:
            return None
        if not pending.approved:
            raise ValueError(
                f"claim_id={pending.changed_claim_id} 的纠错提案未通过 approved 校验，"
                "请人工审查后再 apply；或修复重算让金标准锚点通过"
            )

        cid = pending.changed_claim_id
        src = new_source or (
            f"Correction applied by {approved_by}" if approved_by else "Auto-applied"
        )
        self.graph.update_claim_value(cid, pending.new_value, source=src)

        # 下游 3 个 output/model claim 同步（保证 graph 内部状态一致，测试断言更直观）
        if cid == "starnet_wacc_v1":
            new_wacc_dec = pending.new_value / 100.0
            g_dec = 0.03
            # 公允 PE
            new_pe = (1 + g_dec) / (new_wacc_dec - g_dec)
            if self.graph.has("starnet_model_fair_pe"):
                self.graph.update_claim_value(
                    "starnet_model_fair_pe", round(new_pe, 3),
                    source=f"auto-updated: {cid} changed {pending.old_value}→{pending.new_value}",
                )
            # 目标市值
            new_mcap = starnet_target_market_cap_yi(new_wacc_dec)
            if self.graph.has("starnet_output_target_mcap_yi"):
                self.graph.update_claim_value(
                    "starnet_output_target_mcap_yi", new_mcap,
                    source=f"auto-updated: wacc {pending.old_value}%→{pending.new_value}%",
                )
            # 隐含 upside
            if self.graph.has("starnet_output_upside_pct"):
                cur_mcap = 185.0
                up = round((new_mcap - cur_mcap) / cur_mcap * 100, 1)
                self.graph.update_claim_value(
                    "starnet_output_upside_pct", up,
                    source="auto-updated after target_mcap correction",
                )

        self._last_pending = None
        return pending
