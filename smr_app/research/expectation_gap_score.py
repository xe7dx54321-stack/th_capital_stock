"""
主题预期差 8 维度打分器（Expectation Gap Scorer）

功能说明：
    阶段 7「主题预期差筛选 V1」的核心打分器。
    不是 LLM 直接给分，而是结构化数据 → 确定性公式 → 分数。
    8 个维度（来自 master plan 阶段 8）：
        1. 业务纯度（business_purity）
        2. 收入/利润敏感度（revenue_sensitivity）
        3. 预期差证据（expectation_gap_evidence）
        4. 估值弹性（valuation_elasticity）
        5. 市场拥挤度（market_crowding，越低越好，负权重）
        6. 流动性（liquidity）
        7. 催化可验证性（catalyst_verifiability）
        8. 风险 + 数据质量（risk_and_data_quality，越低越好，负权重）

参数说明：
    ExpectationGapInput   - 输入一条主题候选股的打分数据
    ExpectationGapScore   - 输出打分结果 + 分项明细 + 推荐等级
    ExpectationGapScorer.score(candidate, market_data, evidence) → ExpectationGapScore

返回值说明：
    ExpectationGapScore：
        - total_score      - 0~100 的总分（100 最值得关注）
        - dimension_scores - dict，每个维度的单项 0~100 分和权重
        - recommendation   - 5 档：strong_focus / focus / watch / monitor / skip
        - degraded         - 数据是否不足导致降级
        - degradation_reasons - 降级原因清单
        - watch_list       - 需要验证的待办（小白一眼知道接下来补什么）

异常处理：
    - 缺少 market_cap / avg_turnover 时：对应维度 0 分或中性分，整体 degraded=True
    - 任何值超出 [0,1] 区间时自动 clip（不会崩）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


# ============================================================================
# 维度权重（加起来 = 1.00）
# 小白讲解：这就是 8 个维度的"占分比例"，像考试每道大题多少分一样。
#           业务纯度和催化可验证性占比更高，因为"沾不沾边"是最重要的。
# ============================================================================

_GAP_WEIGHTS: dict[str, float] = {
    "business_purity":          0.20,   # 20 分
    "revenue_sensitivity":      0.12,   # 12 分
    "expectation_gap_evidence": 0.15,   # 15 分（市场不看好 + 有前瞻证据 = 预期差）
    "valuation_elasticity":     0.10,   # 10 分
    "market_crowding":          0.12,   # 12 分（负向：越拥挤扣越多）
    "liquidity":                0.10,   # 10 分
    "catalyst_verifiability":   0.16,   # 16 分（催化越能验证越靠谱）
    "risk_and_data_quality":    0.05,   # 5 分（负向：风险越多扣越多）
}


# ============================================================================
# 数据结构
# ============================================================================

@dataclass
class DimensionBreakdown:
    """单个维度的打分细节"""
    dimension_id: str          # 例如 "business_purity"
    dimension_label: str       # 中文名"业务纯度"
    raw_score_0_1: float       # 原始分 0~1
    weighted_score: float      # 加权分 = raw_score * weight * 100
    weight: float              # 维度权重
    note: str = ""             # 文字解释，例如"纯度 80%，给满分"


@dataclass
class ExpectationGapInput:
    """
    打分输入：每只股票一份

    字段说明（小白版）：
        business_purity_01  - 业务纯度 0~1（1 表示 100% 收入来自主题）
        revenue_sensitivity_01 - 主题增长 10% → 公司收入增长多少（0~1）
        mkt_consensus_bullish_ratio - 一致预期看多占比 0~1（0.8 表示 80% 券商看多）
        forward_implied_cagr - 股价隐含的远期增速（小数，0.2=20%）
        management_guided_cagr - 公司/行业指引增速（小数，0.3=30%）
          → 预期差 = guidance - implied（越大说明市场低估越多）
        pe_ttm / pb_mrq       - 估值（用于估值弹性）
        turnover_rate_20d     - 20 日换手率（小数，0.05 = 5%），用于拥挤度
        avg_turnover_yi       - 20 日均成交额（亿元），用于流动性
        market_cap_yi         - 市值（亿元），用于流动性
        catalyst_count        - 未来 90 天内可验证催化数量（≥1 的数字）
        catalysts_verified    - 已验证催化数量
        risk_item_count       - 已识别核心风险项数
        data_completeness     - 数据完整度 0~1（缺字段就降低）
    """
    ticker: str
    name: str = ""
    business_purity_01: float = 0.0
    revenue_sensitivity_01: float = 0.0
    mkt_consensus_bullish_ratio: Optional[float] = None
    forward_implied_cagr: Optional[float] = None
    management_guided_cagr: Optional[float] = None
    pe_ttm: Optional[float] = None
    pb_mrq: Optional[float] = None
    turnover_rate_20d: Optional[float] = None
    avg_turnover_yi: Optional[float] = None
    market_cap_yi: Optional[float] = None
    catalyst_count: int = 0
    catalysts_verified: int = 0
    risk_item_count: int = 0
    data_completeness: float = 0.0


@dataclass
class ExpectationGapScore:
    """
    打分结果

    字段说明：
        total_score          - 0~100 总分
        recommendation       - 推荐等级（strong_focus/focus/watch/monitor/skip）
        recommendation_label - 中文推荐等级
        dimension_scores     - 8 维度明细
        degraded             - 数据是否降级
        degradation_reasons  - 降级原因
        watch_list           - 待补充信息清单
        created_at           - ISO 时间
    """
    ticker: str
    name: str = ""
    total_score: float = 0.0
    recommendation: str = "monitor"
    recommendation_label: str = "观察"
    dimension_scores: dict[str, DimensionBreakdown] = field(default_factory=dict)
    degraded: bool = False
    degradation_reasons: list[str] = field(default_factory=list)
    watch_list: list[str] = field(default_factory=list)
    created_at: str = ""


# ============================================================================
# 推荐等级阈值（总分 0~100）
# ============================================================================

_RECOMMENDATION_BANDS: list[tuple[int, str, str]] = [
    (80, "strong_focus", "重点关注（预期差强）"),
    (65, "focus",        "关注（预期差明确）"),
    (50, "watch",        "跟踪（有一定预期差）"),
    (30, "monitor",      "观察（预期差胶着）"),
    (0,  "skip",         "跳过（预期差弱或数据不足）"),
]


# ============================================================================
# 核心打分器
# ============================================================================

class ExpectationGapScorer:
    """
    8 维度预期差打分器

    小白讲解：
        就像一份考试卷，8 道大题，每道有自己的"分值占比"。
        每道大题根据结构化数据（不是 LLM 主观）算出 0~1 的原始分，
        乘上权重 ×100 就是加权分；8 道加起来是总分 0~100。
        总分高的进入"重点关注"，低的进"跳过"。
        缺数据不会得高分，但会明确降级和列待办。
    """

    WEIGHTS: dict[str, float] = _GAP_WEIGHTS
    DIM_LABELS: dict[str, str] = {
        "business_purity":          "业务纯度",
        "revenue_sensitivity":      "收入/利润敏感度",
        "expectation_gap_evidence": "预期差证据",
        "valuation_elasticity":     "估值弹性",
        "market_crowding":          "市场拥挤度",
        "liquidity":                "流动性",
        "catalyst_verifiability":   "催化可验证性",
        "risk_and_data_quality":    "风险与数据质量",
    }

    # ------------------------------------------------------------------
    # 对外入口
    # ------------------------------------------------------------------
    def score(self, inp: ExpectationGapInput) -> ExpectationGapScore:
        """
        对单只候选股算预期差总分

        参数：
            inp - ExpectationGapInput（字段越多越好，缺的自动按最低档或中性处理）

        返回：
            ExpectationGapScore，永远非 None
        """
        reasons: list[str] = []
        watch: list[str] = []

        # Clip 关键 0~1 字段，避免越界
        def _clip01(x: Optional[float], default: float) -> float:
            if x is None:
                return default
            try:
                f = float(x)
            except (TypeError, ValueError):
                return default
            if f < 0.0:
                return 0.0
            if f > 1.0:
                return 1.0
            return f

        pur = _clip01(inp.business_purity_01, 0.0)
        sens = _clip01(inp.revenue_sensitivity_01, 0.0)
        comp = _clip01(inp.data_completeness, 0.0)
        if comp < 0.5:
            reasons.append(f"数据完整度仅 {comp:.0%}，不足 50% → 整体降级")
            watch.append("补齐：一致预期(consensus)、隐含CAGR、20日换手率、估值")

        raw_scores: dict[str, float] = {}
        notes: dict[str, str] = {}

        # ---- 1. 业务纯度：直接映射 0~1 ----
        raw_scores["business_purity"] = pur
        if pur >= 0.8:
            notes["business_purity"] = f"纯度 {pur:.0%}，主题高度纯粹"
        elif pur >= 0.4:
            notes["business_purity"] = f"纯度 {pur:.0%}，部分沾边"
        else:
            notes["business_purity"] = f"纯度 {pur:.0%}，业务关联度低"

        # ---- 2. 收入/利润敏感度：直接映射 ----
        raw_scores["revenue_sensitivity"] = sens
        notes["revenue_sensitivity"] = (
            f"收入弹性 {sens:.0%}（主题涨 10% → 公司收入增 {sens*10:.1f}%）"
        )

        # ---- 3. 预期差证据：guidance - implied 越大越好；consensus_bullish 越低越容易出预期差 ----
        evidence, note3 = self._expectation_gap_raw(
            implied=inp.forward_implied_cagr,
            guided=inp.management_guided_cagr,
            bullish_ratio=inp.mkt_consensus_bullish_ratio,
        )
        raw_scores["expectation_gap_evidence"] = evidence
        notes["expectation_gap_evidence"] = note3
        if inp.forward_implied_cagr is None or inp.management_guided_cagr is None:
            watch.append("补齐：一致预期远期增速(implied CAGR) / 公司指引增速(guided CAGR)")

        # ---- 4. 估值弹性：小盘 + 中低 PE/PB 弹性最高 ----
        elastic, note4 = self._elasticity_raw(
            pe=inp.pe_ttm, pb=inp.pb_mrq, mcap=inp.market_cap_yi,
        )
        raw_scores["valuation_elasticity"] = elastic
        notes["valuation_elasticity"] = note4
        if inp.pe_ttm is None and inp.pb_mrq is None:
            watch.append("补齐：PE TTM / PB MRQ（估值弹性无法准确评估）")

        # ---- 5. 拥挤度：越低越好（负向）----
        crowd, note5 = self._crowding_raw(inp.turnover_rate_20d)
        raw_scores["market_crowding"] = crowd
        notes["market_crowding"] = note5
        if inp.turnover_rate_20d is None:
            watch.append("补齐：20 日换手率（拥挤度无法评估）")

        # ---- 6. 流动性：成交额 ≥ 门槛 才算 1 ----
        liq, note6 = self._liquidity_raw(
            turnover_yi=inp.avg_turnover_yi, mcap=inp.market_cap_yi,
        )
        raw_scores["liquidity"] = liq
        notes["liquidity"] = note6
        if inp.avg_turnover_yi is None:
            watch.append("补齐：20 日日均成交额（流动性门槛无法确认）")

        # ---- 7. 催化可验证性：催化数越多、已验证比越高 → 分越高 ----
        cat, note7 = self._catalyst_raw(
            catalyst_count=max(0, int(inp.catalyst_count or 0)),
            catalysts_verified=max(0, int(inp.catalysts_verified or 0)),
        )
        raw_scores["catalyst_verifiability"] = cat
        notes["catalyst_verifiability"] = note7
        if inp.catalyst_count == 0:
            watch.append("补充：未来 90 天可验证催化事件清单（产品/订单/认证/工厂）")

        # ---- 8. 风险 & 数据质量（负向：risk 越少 + data 越全 → 分越高）----
        risk, note8 = self._risk_data_raw(
            risk_count=max(0, int(inp.risk_item_count or 0)),
            completeness=comp,
        )
        raw_scores["risk_and_data_quality"] = risk
        notes["risk_and_data_quality"] = note8
        if inp.risk_item_count == 0:
            watch.append("提示：尚未列示核心风险，建议人工补充 2~3 条")

        # ---- 汇总加权分 ----
        total = 0.0
        dim_breakdown: dict[str, DimensionBreakdown] = {}
        for dim_id, weight in _GAP_WEIGHTS.items():
            raw = raw_scores.get(dim_id, 0.0)
            weighted = round(raw * weight * 100.0, 2)
            total += weighted
            dim_breakdown[dim_id] = DimensionBreakdown(
                dimension_id=dim_id,
                dimension_label=self.DIM_LABELS.get(dim_id, dim_id),
                raw_score_0_1=round(raw, 3),
                weighted_score=weighted,
                weight=weight,
                note=notes.get(dim_id, ""),
            )

        total = round(total, 2)

        # ---- 推荐等级 ----
        rec, rec_label = self._band(total, degraded=bool(reasons))
        degraded = len(reasons) > 0 or comp < 0.5

        # 最终得分被降级惩罚：若 degraded → 总分 × 0.8
        if degraded and total > 0:
            total = round(total * 0.8, 2)
            rec, rec_label = self._band(total, degraded=True)

        return ExpectationGapScore(
            ticker=inp.ticker,
            name=inp.name,
            total_score=total,
            recommendation=rec,
            recommendation_label=rec_label,
            dimension_scores=dim_breakdown,
            degraded=degraded,
            degradation_reasons=reasons,
            watch_list=watch,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # 内部：7 个维度的打分小函数（每个返回 (0~1 原始分, 文字注释)）
    # ------------------------------------------------------------------

    @staticmethod
    def _expectation_gap_raw(
        implied: Optional[float],
        guided: Optional[float],
        bullish_ratio: Optional[float],
    ) -> tuple[float, str]:
        """
        预期差证据打分（0~1）

        逻辑：
            - guidance > implied → 公司指引比市场隐含快 → 潜在超预期（加分）
            - bullish_ratio 低 → 市场一致看空，超预期概率大（反向加分）
            - 两个数据都没有 → 0.3（中性偏低，不算有预期差）
        """
        score_delta = 0.0
        note_parts = []
        if implied is not None and guided is not None:
            delta = guided - implied   # 0.1 = 指引比隐含快 10 个点
            # delta 映射：≥0.10 → 1.0，0 → 0.5，≤-0.10 → 0.0
            mapped = 0.5 + (delta / 0.20)
            mapped = min(max(mapped, 0.0), 1.0)
            score_delta = mapped
            direction = "市场低估" if delta >= 0 else "市场高估"
            note_parts.append(f"指引增速 {guided*100:.1f}% vs 隐含 {implied*100:.1f}%（{direction} {abs(delta)*100:.1f}pp）")
        else:
            score_delta = 0.3  # 没数据 → 不默认有预期差
            note_parts.append("缺 implied/guided 增速数据，按中性偏低处理")

        # 一致预期看多率：看多越多 → 预期差越难兑现（反向）
        if bullish_ratio is not None:
            # bullish_ratio=0.9(90%看多) → 0.2；bullish_ratio=0.3 → 0.9
            rev = 1.0 - ((max(0.0, min(1.0, bullish_ratio)) - 0.2) / 0.8)
            rev = min(max(rev, 0.0), 1.0)
            score_delta = 0.6 * score_delta + 0.4 * rev
            note_parts.append(f"一致看多占比 {bullish_ratio*100:.0f}%（越低越容易出预期差）")

        return round(score_delta, 3), "；".join(note_parts)

    @staticmethod
    def _elasticity_raw(
        pe: Optional[float],
        pb: Optional[float],
        mcap: Optional[float],
    ) -> tuple[float, str]:
        """
        估值弹性打分（小盘 + 中低估值 → 弹性高）

        简化规则：
            mcap < 200 亿 → 小盘系数 1
            200~1000 亿 → 0.7
            >1000 亿 → 0.4
            PE 15~40 或 PB 1.5~5.0 → 中估值（最好），PE/PB 缺 → 0.5 中性
        """
        if mcap is None:
            mcap_score = 0.5
            mcap_note = "市值未填，按中性"
        elif mcap < 200:
            mcap_score = 1.0
            mcap_note = f"小盘（{mcap:.0f} 亿）弹性高"
        elif mcap <= 1000:
            mcap_score = 0.7
            mcap_note = f"中盘（{mcap:.0f} 亿）弹性中等"
        else:
            mcap_score = 0.4
            mcap_note = f"大盘（{mcap:.0f} 亿）弹性较弱"

        val_score = 0.5
        val_note = "估值未填，按中性"
        if pe is not None or pb is not None:
            pe_ok = (pe is not None and 10 <= pe <= 45)
            pb_ok = (pb is not None and 1 <= pb <= 6)
            if pe_ok or pb_ok:
                val_score = 0.9
            elif pe is not None and pe < 10:
                val_score = 0.6  # 极便宜但可能有坑
            elif pe is not None and pe > 80:
                val_score = 0.3  # 泡沫太大
            else:
                val_score = 0.5
            val_note = "PE={} / PB={}".format(
                f"{pe:.1f}" if pe is not None else "N/A",
                f"{pb:.2f}" if pb is not None else "N/A",
            )
        score = round(0.55 * mcap_score + 0.45 * val_score, 3)
        note = f"{mcap_note}；{val_note}"
        return score, note

    @staticmethod
    def _crowding_raw(turnover_20d: Optional[float]) -> tuple[float, str]:
        """
        市场拥挤度（负向：越低越安全 → 分越高）

        规则：
            0.5% 以下 → 1.0（非常不拥挤）
            1%   → 0.8
            3%   → 0.4
            8%+  → 0.1（极其拥挤）
            None → 0.5（中性偏保守）
        """
        if turnover_20d is None:
            return 0.5, "换手率缺失，按中性偏保守处理"
        t = max(0.0, float(turnover_20d))
        # 线性插值区间 [0, 0.08] → [1, 0.1]
        if t <= 0:
            score = 1.0
        elif t >= 0.08:
            score = 0.1
        else:
            score = 1.0 - (t / 0.08) * 0.9
        return round(score, 3), f"20 日换手率 {t*100:.2f}%（越低越不拥挤）"

    @staticmethod
    def _liquidity_raw(
        turnover_yi: Optional[float],
        mcap: Optional[float],
    ) -> tuple[float, str]:
        """
        流动性打分（≥ 2 亿/日 就算满分）
        """
        if turnover_yi is None or turnover_yi <= 0:
            if mcap is None:
                return 0.0, "成交额/市值均缺失，流动性无法确认 → 0 分"
            # 用市值兜底：>500 亿的票一般也能成交 >1 亿
            if mcap >= 1000:
                return 0.7, f"缺成交额，按大市值 {mcap:.0f} 亿兜底 0.7"
            if mcap >= 300:
                return 0.5, f"缺成交额，按中市值 {mcap:.0f} 亿兜底 0.5"
            return 0.2, f"缺成交额，小市值 {mcap:.0f} 亿兜底 0.2"
        t = float(turnover_yi)
        if t >= 5:
            return 1.0, f"日均 {t:.1f} 亿 → 流动性充裕"
        if t >= 2:
            return 0.85, f"日均 {t:.1f} 亿 → 合格"
        if t >= 1:
            return 0.55, f"日均 {t:.1f} 亿 → 勉强"
        if t >= 0.5:
            return 0.3, f"日均 {t:.1f} 亿 → 偏弱"
        return 0.1, f"日均 {t:.2f} 亿 → 严重不足"

    @staticmethod
    def _catalyst_raw(catalyst_count: int, catalysts_verified: int) -> tuple[float, str]:
        """
        催化可验证性打分（数量 + 已验证比）
        """
        if catalyst_count <= 0:
            return 0.1, "无待验证催化 → 低分"
        # 数量项：≥ 3 项 → 1.0；1 项 → 0.4
        cnt = min(catalyst_count / 3.0, 1.0)
        # 验证比：越高越可信
        verified_ratio = (catalysts_verified / catalyst_count) if catalyst_count > 0 else 0.0
        score = 0.55 * cnt + 0.45 * verified_ratio
        return round(score, 3), (
            f"未来催化 {catalyst_count} 项；已验证 {catalysts_verified} 项"
            f"（已验证比 {verified_ratio:.0%}）"
        )

    @staticmethod
    def _risk_data_raw(risk_count: int, completeness: float) -> tuple[float, str]:
        """
        风险 & 数据质量（负向）：
            - 0 项风险 → 可能没做研究，给 0.3（不鼓励"不写风险=满分"）
            - 2~3 项合适 → 0.9
            - ≥ 6 项太多 → 0.4（雷太多）
            - 再乘 data_completeness（缺数据就整体打折）
        """
        if risk_count == 0:
            risk_score = 0.3
            risk_note = "无风险项 → 惩罚性 0.3（建议人工补充）"
        elif 2 <= risk_count <= 4:
            risk_score = 0.9
            risk_note = f"{risk_count} 条风险，数量合适"
        elif risk_count >= 6:
            risk_score = 0.4
            risk_note = f"{risk_count} 条风险过多，密集爆雷概率上升"
        else:
            risk_score = 0.7
            risk_note = f"{risk_count} 条风险，偏少"
        # 数据完整度加权：越全越好
        final = round(risk_score * (0.4 + 0.6 * completeness), 3)
        return final, f"{risk_note}；数据完整度 {completeness:.0%}"

    @staticmethod
    def _band(total: float, degraded: bool = False) -> tuple[str, str]:
        """按总分档位算推荐等级"""
        for cutoff, rec, label in _RECOMMENDATION_BANDS:
            if total >= cutoff:
                if degraded and rec == "strong_focus":
                    return "focus", "关注（数据降级）"
                return rec, label
        return "skip", "跳过（无分）"
