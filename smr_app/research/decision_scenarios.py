"""
决策情景分析 - 四方案换仓决策引擎

功能说明：
    基于 ComparisonMatrix（同口径比较矩阵）和用户偏好，生成四种决策方案：
    1. continue_hold   - 继续持有（不换）
    2. partial_switch  - 部分换仓（换 X%）
    3. full_switch     - 完全换仓（全部换成 B）
    4. hold_and_wait   - 暂缓（等待更多信号后再决策）

    核心原则（来自 master plan 阶段 5）：
    - 每个方案有明确的"成立条件"和"失效条件"（可验证的、非主观的）
    - 用户偏好只使用明确确认的信息（未确认的偏好不参与打分）
    - 不把"估值便宜/昂贵"直接等同于"应该买入/卖出"
    - 分批节奏和需要监控的领先指标确定性输出
    - 明确声明不执行真实交易（只是研究备忘录）

参数说明：
    DecisionInput - 决策输入（比较矩阵 + 用户偏好 + 换仓约束）
    ScenarioPlanner.generate_scenarios(decision_input) - 生成四方案
    compute_partial_ratio(matrix, preference) - 计算部分换仓比例
    generate_monitoring_list(matrix) - 生成需要监控的领先指标清单

返回值说明：
    DecisionOutput 数据类，包含：
    - scenarios: dict[方案名] = DecisionScenario（名称、解释、成立条件、失效条件、分批节奏、打分）
    - recommended: 推荐方案名（基于打分但需用户确认，不自动执行）
    - monitoring_indicators: 需要监控的领先指标清单
    - execution_warning: 明确"不执行真实交易"的声明
    - preference_used: 本次决策中实际使用了哪些用户偏好（透明性）
    - warnings: 警告列表

异常处理：
    关键输入缺失时，相关方案 downgrade（不取消，只降低置信度并标注原因）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .comparison_matrix import ComparisonMatrix


# ============================================================================
# 数据结构定义
# ============================================================================


@dataclass
class UserPreference:
    """
    用户偏好（只使用明确确认的字段；None 表示用户未表态，不做臆测）

    小白讲解：
        这是用户的"个人需求清单"——比如"我最多亏 10% 就走"、
        "我持有期 6 个月"、"我不碰亏损股"。
        所有字段都是 Optional：用户没明确说的就留 None，
        DecisionPlanner 看到 None 就跳过，**不会**替用户假设。
    """
    # ---- 持有期与收益目标 ----
    holding_horizon_months: Optional[int] = None   # 计划持有期（月），如 12 = 一年
    annual_return_target: Optional[float] = None   # 年化收益目标（小数，0.20 = 20%）
    # ---- 风险偏好 ----
    max_drawdown_tolerance: Optional[float] = None # 最大回撤容忍（小数，0.15 = 15%）
    accept_loss_stock: Optional[bool] = None       # 是否接受亏损股，None = 未表态
    accept_high_crowding: Optional[bool] = None    # 是否接受高拥挤度交易
    # ---- 换仓成本约束 ----
    avoid_short_term_tax: Optional[bool] = None    # 是否规避短期持有税费（A股印花税/佣金）
    min_switch_ratio: Optional[float] = None       # 最小换仓比例（小数，0.25 = 至少换 25%）
    max_switch_ratio: Optional[float] = None       # 最大换仓比例（小数，1.00 = 最多全换）
    # ---- 行业/风格偏好 ----
    allow_cross_sector: Optional[bool] = None      # 是否允许跨行业换仓（None = 允许默认）
    prefer_industry_leader: Optional[bool] = None  # 是否偏好行业龙头
    avoid_negative_roe: Optional[bool] = None      # 是否拒绝 ROE<=0 的标的
    # ---- 流动性约束 ----
    min_daily_turnover_yi: Optional[float] = None  # 最低日成交要求（亿元），不足则不考虑大比例换仓


@dataclass
class DecisionCondition:
    """
    一个可验证的条件（成立条件 / 失效条件）

    小白讲解：
        这就像合同条款——"当 2026Q3 海光 DCU 出货量 >= 45 万颗，
        完全换仓方案成立"。
        description 是人能看懂的话，
        indicator 是要监控的指标名（"hygon_dcu_shipment_2026q3"），
        threshold 是阈值（45），unit 是单位（"万颗"），
        direction 是 "gte"/"lte"/"eq"。
        met = True 表示当前数据已满足该条件。
    """
    description: str                                # 中文描述（用于报告）
    indicator: str = ""                             # 指标 ID（用于监控）
    threshold: Any = None                           # 阈值
    current_value: Any = None                       # 当前值（如果可得）
    unit: str = ""                                  # 单位
    direction: str = ""                             # "gte" / "lte" / "eq" / "contains"
    met: Optional[bool] = None                      # 当前是否满足，None = 无法判断
    source: str = ""                                # 来源标签


@dataclass
class PacingStep:
    """
    分批换仓的一步

    小白讲解：
        一次换仓不要 all in，而是分几批。
        每一批写清楚：换多少（ratio）、什么时候执行（trigger）、
        监控什么指标（indicator）、为什么要这样分（rationale）。
    """
    step_index: int                                 # 第几步（1, 2, 3...）
    ratio: float                                    # 这一步占总换仓比例（小数，0.33 = 1/3）
    trigger: str                                    # 触发条件（中文，如"立即"、"2026Q2 财报后"、"价格回调 8%"）
    indicator: str = ""                             # 触发时监控的指标
    rationale: str = ""                             # 这样分的原因


@dataclass
class DecisionScenario:
    """
    一个决策方案（继续持有 / 部分换仓 / 完全换仓 / 暂缓）

    小白讲解：
        这是"医生给的 4 个治疗方案"。
        每个方案有：
        - 叫什么、大概怎么做（description）
        - 什么情况下这个方案是对的（成立条件 valid_conditions）
        - 什么情况下这个方案就废了（失效条件 invalid_conditions）
        - 分几步做（pacing）
        - 综合分数（score，0~100，仅排序参考，不直接"谁高就执行谁"）
        - 数据置信度（degraded 说明这个方案的判断依据不足）
    """
    scenario_id: str                                # "continue_hold" / "partial_switch" / "full_switch" / "hold_and_wait"
    name: str                                       # 中文名
    description: str                                # 方案说明
    valid_conditions: list[DecisionCondition] = field(default_factory=list)
    invalid_conditions: list[DecisionCondition] = field(default_factory=list)
    pacing: list[PacingStep] = field(default_factory=list)
    score: int = 0                                  # 0~100，排序参考
    confidence: float = 0.0                         # 0.0~1.0，数据充分程度
    degraded: bool = False                          # 是否因数据不足降级
    degradation_reasons: list[str] = field(default_factory=list)
    expected_switch_ratio: Optional[float] = None   # 总换仓比例（0~1，只有 partial/full 有值）
    rationale: str = ""                             # 推荐此方案的核心理由（1 句话）


@dataclass
class MonitoringIndicator:
    """
    需要持续跟踪的领先指标

    小白讲解：
        "决策不是一锤子买卖，要盯着这几个红绿灯。"
        每个领先指标有：名称、为什么重要（看它就能提前发现方案失效）、
        多久看一次（频率）、当前值、预警阈值。
    """
    indicator_id: str
    name: str
    why_it_matters: str
    frequency: str = ""                              # "每日" / "每周" / "每季财报"
    current_value: Any = None
    unit: str = ""
    warn_threshold: Any = None                       # 到这个值就该重新评估
    direction: str = ""                              # "above"/"below"
    applies_to_scenarios: list[str] = field(default_factory=list)


@dataclass
class DecisionOutput:
    """
    决策输出（四方案 + 推荐 + 监控 + 免责）

    小白讲解：
        这是"会诊报告"——四个方案各自的优缺点，
        哪个更合适（recommended）、要盯着哪些红绿灯，
        以及最重要的免责声明（明确不执行真实交易）。
    """
    a_ticker: str
    b_ticker: str
    scenarios: dict[str, DecisionScenario] = field(default_factory=dict)
    recommended: str = ""                           # 推荐方案 ID（仅建议，用户确认）
    confidence_level: str = ""                      # "高"/"中"/"低"
    monitoring_indicators: list[MonitoringIndicator] = field(default_factory=list)
    preference_used: list[str] = field(default_factory=list)   # 实际用到的用户偏好项（透明）
    preference_skipped: list[str] = field(default_factory=list)  # 未使用的偏好（"未明确表态"）
    execution_warning: str = ""
    warnings: list[str] = field(default_factory=list)
    data_gaps: list[str] = field(default_factory=list)


# ============================================================================
# 决策情景规划器
# ============================================================================


# 四方案元数据
_SCENARIO_META = {
    "continue_hold": ("继续持有", "保留当前 A 标的全部仓位，不换入 B"),
    "partial_switch": ("部分换仓", "将 A 的一部分仓位换成 B，保留部分 A 暴露"),
    "full_switch":    ("完全换仓", "A 标的全部卖出，换入等市值的 B 标的"),
    "hold_and_wait":  ("暂缓决策", "当前不操作，等待核心验证条件出现后再评估"),
}


class ScenarioPlanner:
    """
    决策情景规划器

    小白讲解：
        这是"会诊主任"——拿到比较矩阵和用户偏好后，
        给出四个方案，每个方案有：
        - 它为什么成立、什么情况下就不对了
        - 如果要执行，分几步（分批）
        - 综合打分（只用于排序，不直接决定）
        最后，主任给出一个"推荐方案"但明确说：
        "这只是建议，你要确认。系统不替你下单。"
    """

    def __init__(self, *, enable_real_trade: bool = False):
        """
        参数:
            enable_real_trade: 是否允许真实交易（**强制 False**，master plan 明确不执行真实交易）
        """
        if enable_real_trade:
            raise ValueError("根据 master plan 阶段 5 约束，本系统不执行真实交易。")
        self._enable_real_trade = False

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------

    def generate_scenarios(
        self,
        matrix: ComparisonMatrix,
        preference: Optional[UserPreference] = None,
    ) -> DecisionOutput:
        """
        基于比较矩阵和用户偏好生成四方案决策

        参数:
            matrix: ComparisonMatrix（12 维度同口径对比）
            preference: 用户偏好，None 时全部视为"未明确表态"

        返回:
            DecisionOutput
        """
        output = DecisionOutput(
            a_ticker=matrix.a_ticker,
            b_ticker=matrix.b_ticker,
            execution_warning=(
                "【重要】本备忘录仅为研究记录，不构成投资建议。"
                "系统明确不执行任何真实交易。所有决策需用户人工确认并自行承担后果。"
            ),
        )
        warnings: list[str] = list(matrix.warnings)
        preference = preference or UserPreference()

        # === 1. 记录用户偏好使用情况（透明性）===
        used, skipped = self._catalog_preference_usage(preference)
        output.preference_used = used
        output.preference_skipped = skipped

        # === 2. 数据完整度评估 ===
        data_sufficient = matrix.overall_completeness >= 0.55 and matrix.temporal_alignment_pass
        if not data_sufficient:
            warnings.append(
                f"数据完整度仅 {matrix.overall_completeness:.0%}，"
                "时点对齐=" + ("通过" if matrix.temporal_alignment_pass else "未通过")
                + "；四方案将整体降级。"
            )

        # === 3. 生成 4 个方案 ===
        output.scenarios["continue_hold"] = self._plan_continue_hold(
            matrix, preference, data_sufficient, warnings,
        )
        output.scenarios["partial_switch"] = self._plan_partial_switch(
            matrix, preference, data_sufficient, warnings,
        )
        output.scenarios["full_switch"] = self._plan_full_switch(
            matrix, preference, data_sufficient, warnings,
        )
        output.scenarios["hold_and_wait"] = self._plan_hold_and_wait(
            matrix, preference, data_sufficient, warnings,
        )

        # === 4. 推荐方案（按分数排序 + 约束叠加）===
        rec_id, confidence = self._select_recommended(output.scenarios, preference, warnings)
        output.recommended = rec_id
        output.confidence_level = confidence

        # === 5. 监控清单 ===
        output.monitoring_indicators = self._generate_monitoring_list(matrix)

        # === 6. 收尾 ===
        output.warnings = warnings
        output.data_gaps = list(matrix.data_gaps)

        return output

    # ------------------------------------------------------------------
    # 内部：用户偏好了目录（透明性）
    # ------------------------------------------------------------------

    @staticmethod
    def _catalog_preference_usage(pref: UserPreference) -> tuple[list[str], list[str]]:
        """把用户偏好分成"实际使用/已明确"和"未表态跳过"两组，保证透明"""
        used: list[str] = []
        skipped: list[str] = []
        # 列出所有字段，按语义判断是否"用户明确说了"
        all_fields = [
            ("holding_horizon_months", "计划持有期"),
            ("annual_return_target", "年化收益目标"),
            ("max_drawdown_tolerance", "最大回撤容忍"),
            ("accept_loss_stock", "是否接受亏损股"),
            ("accept_high_crowding", "是否接受高拥挤度"),
            ("avoid_short_term_tax", "是否规避短期税费"),
            ("min_switch_ratio", "最小换仓比例"),
            ("max_switch_ratio", "最大换仓比例"),
            ("allow_cross_sector", "是否允许跨行业"),
            ("prefer_industry_leader", "是否偏好龙头"),
            ("avoid_negative_roe", "是否拒绝负 ROE"),
            ("min_daily_turnover_yi", "最低日成交要求"),
        ]
        for attr, label in all_fields:
            val = getattr(pref, attr, None)
            if val is None:
                skipped.append(f"{label}：未明确表态，按中性处理")
            else:
                used.append(f"{label} = {val}")
        return used, skipped

    # ------------------------------------------------------------------
    # 四个方案的独立构造函数
    # ------------------------------------------------------------------

    def _plan_continue_hold(self, m: ComparisonMatrix, pref: UserPreference,
                            sufficient: bool, warnings: list[str]) -> DecisionScenario:
        """方案 1：继续持有 A"""
        sid = "continue_hold"
        name, desc = _SCENARIO_META[sid]
        s = DecisionScenario(scenario_id=sid, name=name, description=desc, expected_switch_ratio=0.0)
        degrade_reasons: list[str] = []

        # ---- 打分：A 比 B 好的方面越多，分数越高 ----
        score, signals = self._score_by_dimensions(m, favor="A")
        s.score = score

        # ---- 成立条件（此方案成立需要满足的）----
        s.valid_conditions = self._build_hold_valid(m, pref)
        # ---- 失效条件（一旦触发，就不该继续持有 A）----
        s.invalid_conditions = self._build_hold_invalid(m, pref)

        # ---- 分批：不换仓，就没有分批。但有"再评估时点" ----
        s.pacing = [PacingStep(1, 0.0, trigger="不操作；按监控清单每季度复盘",
                               indicator="quarterly_review",
                               rationale="不换仓但需要定期检查 A 和 B 的相对趋势是否反转")]

        # ---- 置信度与降级 ----
        s.confidence = min(1.0, (signals["a_better"] + signals["tied"]) / max(1, signals["total"]))
        if not sufficient:
            s.degraded = True
            degrade_reasons.append("对比数据不足 55% 或时点未对齐")
        if signals["degraded_rows"] > 0:
            degrade_reasons.append(f"{signals['degraded_rows']} 个对比维度降级")
        # 用户约束：收益目标无法通过 A 的估值上行空间达到
        val_row = m.get_row("valuation")
        if (pref.annual_return_target is not None and val_row and not val_row.a.degraded
                and isinstance(val_row.a.value, dict) and val_row.a.value.get("upside_potential") is not None):
            upside = val_row.a.value["upside_potential"]
            horizon = pref.holding_horizon_months or 12
            annualized = (1 + upside) ** (12 / horizon) - 1 if horizon > 0 else 0
            if annualized < pref.annual_return_target:
                s.valid_conditions.append(DecisionCondition(
                    description=f"A 标的年化上行空间 {annualized*100:.1f}% 低于用户目标 {pref.annual_return_target*100:.0f}%，"
                                "需接受低收益或主动下调目标",
                    indicator="a_upside_vs_target",
                    threshold=pref.annual_return_target,
                    current_value=round(annualized, 4),
                    unit="%/年", direction="gte", met=False,
                    source="preference + phase4_valuation",
                ))
                degrade_reasons.append("A 的上行空间达不到用户收益目标")
        s.degraded = s.degraded or bool(degrade_reasons)
        s.degradation_reasons = degrade_reasons
        if s.degraded:
            s.confidence *= 0.6

        s.rationale = (
            f"A 相对占优维度 {signals['a_better']} 项，"
            f"B 相对占优维度 {signals['b_better']} 项，持平 {signals['tied']} 项。"
        )
        return s

    def _plan_partial_switch(self, m: ComparisonMatrix, pref: UserPreference,
                             sufficient: bool, warnings: list[str]) -> DecisionScenario:
        """方案 2：部分换仓（默认 1/3 或用户约束区间）"""
        sid = "partial_switch"
        name, desc = _SCENARIO_META[sid]
        s = DecisionScenario(scenario_id=sid, name=name, description=desc)
        degrade_reasons: list[str] = []

        # ---- 计算换仓比例 ----
        ratio, ratio_reasons = self._compute_partial_ratio(m, pref)
        s.expected_switch_ratio = ratio
        degrade_reasons.extend(ratio_reasons)

        # ---- 打分：A、B 势均力敌但 B 略好时，部分换仓最合适 ----
        score, signals = self._score_by_dimensions(m, favor="balance")
        s.score = score

        # ---- 成立/失效条件 ----
        s.valid_conditions = self._build_partial_valid(m, pref, ratio)
        s.invalid_conditions = self._build_partial_invalid(m, pref, ratio)

        # ---- 分批：默认 3 步 ----
        s.pacing = self._build_partial_pacing(m, ratio)

        # ---- 置信度与降级 ----
        s.confidence = 0.7 if 0.15 <= ratio <= 0.75 else 0.5
        if not sufficient:
            s.degraded = True
            degrade_reasons.append("对比数据不足或时点未对齐")
        if signals["degraded_rows"] > 4:
            degrade_reasons.append(f"{signals['degraded_rows']} 个维度降级，比例计算不确定性高")
        s.degraded = s.degraded or bool(degrade_reasons)
        s.degradation_reasons = degrade_reasons
        if s.degraded:
            s.confidence *= 0.6

        s.rationale = (
            f"A/B 各有优劣，部分换仓平衡风险与收益；计划换仓 {ratio*100:.0f}%。"
        )
        return s

    def _plan_full_switch(self, m: ComparisonMatrix, pref: UserPreference,
                          sufficient: bool, warnings: list[str]) -> DecisionScenario:
        """方案 3：完全换仓（A 全换成 B）"""
        sid = "full_switch"
        name, desc = _SCENARIO_META[sid]
        s = DecisionScenario(scenario_id=sid, name=name, description=desc, expected_switch_ratio=1.0)
        degrade_reasons: list[str] = []

        # ---- 打分：B 明显优于 A 时分数高 ----
        score, signals = self._score_by_dimensions(m, favor="B")
        s.score = score

        # ---- 成立/失效条件 ----
        s.valid_conditions = self._build_full_valid(m, pref)
        s.invalid_conditions = self._build_full_invalid(m, pref)

        # ---- 分批：全换也建议分 2 步，避免单点价格风险 ----
        s.pacing = [
            PacingStep(1, 0.5, trigger="立即（或首个工作日）",
                       indicator="execution_price_vs_close",
                       rationale="首批成交 50%，预留回调空间"),
            PacingStep(2, 0.5, trigger="首批成交后 5~10 个交易日或回调 >= 5%",
                       indicator="b_short_term_drawdown",
                       rationale="第二批看价格；避免追高、同时避免踏空"),
        ]

        # ---- 用户约束：max_switch_ratio < 1 时，全换方案直接降级 ----
        if pref.max_switch_ratio is not None and pref.max_switch_ratio < 1.0:
            degrade_reasons.append(
                f"用户明确最大换仓比例 {pref.max_switch_ratio*100:.0f}%，全换方案不满足硬约束"
            )
            s.score = max(0, s.score - 30)
        # ---- 用户约束：跨行业禁止但 A/B 不同行业 ----
        if pref.allow_cross_sector is False:
            a_ind = getattr(m.get_row("industry_position") and m.get_row("industry_position").a.value or {}, "get",
                            lambda *_: None)
            b_ind_dict = (m.get_row("industry_position") or type("R", (), {"b": type("B", (), {"value": None})()})()).b.value
            a_industry = None
            b_industry = None
            row = m.get_row("industry_position")
            if row and isinstance(row.a.value, dict):
                a_industry = row.a.value.get("industry")
            if row and isinstance(row.b.value, dict):
                b_industry = row.b.value.get("industry")
            if a_industry and b_industry and a_industry != b_industry:
                degrade_reasons.append("用户禁止跨行业，但 A/B 不属于同一行业")
                s.score = max(0, s.score - 40)
        # ---- 用户约束：拒绝负 ROE 且 B 的 ROE<=0 ----
        if pref.avoid_negative_roe:
            roe_row = m.get_row("roe")
            if roe_row and not roe_row.b.degraded and roe_row.b.value is not None and roe_row.b.value <= 0:
                degrade_reasons.append("用户拒绝负 ROE，但 B 的 ROE <= 0")
                s.score = 0

        # ---- 数据充分度 ----
        s.confidence = min(1.0, (signals["b_better"] + signals["tied"]) / max(1, signals["total"]))
        if not sufficient:
            s.degraded = True
            degrade_reasons.append("对比数据不足或时点未对齐")
        if signals["degraded_rows"] > 0:
            degrade_reasons.append(f"{signals['degraded_rows']} 个对比维度降级")
        s.degraded = s.degraded or bool(degrade_reasons)
        s.degradation_reasons = degrade_reasons
        if s.degraded:
            s.confidence *= 0.55

        s.rationale = (
            f"B 占优维度 {signals['b_better']} 项，A 占优 {signals['a_better']} 项；"
            "需要确认成立条件全部满足。"
        )
        return s

    def _plan_hold_and_wait(self, m: ComparisonMatrix, pref: UserPreference,
                            sufficient: bool, warnings: list[str]) -> DecisionScenario:
        """方案 4：暂缓决策"""
        sid = "hold_and_wait"
        name, desc = _SCENARIO_META[sid]
        s = DecisionScenario(scenario_id=sid, name=name, description=desc, expected_switch_ratio=0.0)
        degrade_reasons: list[str] = []

        # ---- 打分：数据越不充分、核心条件越悬而未决，暂缓方案分数越高 ----
        gap_weight = len(m.data_gaps) * 4
        if not m.temporal_alignment_pass:
            gap_weight += 15
        # 有多少"不确定"的成立条件（met=None 或 met=False 但重要）
        uncertain_valid_cnt = 0
        # 用 A 方案的成立条件数量近似
        uncertain_valid_cnt += sum(1 for c in self._build_hold_valid(m, pref) if c.met is None)
        s.score = min(100, 25 + gap_weight + uncertain_valid_cnt * 3)

        # ---- 成立条件：数据缺口补齐、核心催化落地之前 ----
        s.valid_conditions = self._build_wait_valid(m)
        s.invalid_conditions = self._build_wait_invalid(m)

        # ---- 分批：只有"后续再评估"一步 ----
        s.pacing = [PacingStep(1, 0.0, trigger=f"等待 {max(1, len(m.data_gaps))} 项核心数据缺口补齐或最近催化落地",
                               indicator="wait_for_data_and_catalysts",
                               rationale="暂缓不是永久不操作，而是等信号更清晰")]

        # ---- 置信度 ----
        s.confidence = 0.85 if len(m.data_gaps) >= 3 else 0.6
        if sufficient:
            s.degraded = False
        else:
            # 暂缓方案在数据不足时反而更可靠，但要记录原因
            s.degraded = False
            degrade_reasons.append("此方案在数据不足时是保守选择，不视为降级")
        s.degradation_reasons = degrade_reasons
        s.rationale = f"当前存在 {len(m.data_gaps)} 项数据缺口，暂缓可避免盲动。"
        return s

    # ------------------------------------------------------------------
    # 打分：基于 12 维度的简单加权（不涉及复杂机器学习，可解释）
    # ------------------------------------------------------------------

    # 每个维度的权重（0~10），越重要越高
    _DIM_WEIGHTS: dict[str, int] = {
        "roe": 10,
        "valuation": 10,
        "implied_growth": 9,
        "revenue_quality": 9,
        "cash_flow": 8,
        "industry_position": 8,
        "crowding": 6,
        "price_action": 5,
        "risks": 7,
        "catalysts": 6,
        "lifecycle": 5,
        "holding_constraints": 0,  # 持仓约束只对 A 适用，不计入相对分
    }

    def _score_by_dimensions(self, m: ComparisonMatrix, favor: str
                             ) -> tuple[int, dict[str, int]]:
        """
        基于 12 维度计算方案基础分 + A/B/持平 统计

        参数:
            favor: "A"= A 优高分给 continue_hold；"B"= B 优高分给 full_switch；
                   "balance"=A/B 越接近高分给 partial_switch
        返回:
            (score 0~100, stats dict)
        """
        a_better = 0
        b_better = 0
        tied = 0
        degraded_rows = 0
        total = 0
        weighted_a = 0.0
        weighted_b = 0.0
        weighted_total = 0.0

        for dim_id in m.all_dimension_ids():
            if dim_id == "holding_constraints":
                continue
            row = m.rows[dim_id]
            total += 1
            if row.a.degraded or row.b.degraded:
                degraded_rows += 1
                continue
            weight = self._DIM_WEIGHTS.get(dim_id, 5)
            weighted_total += weight
            # 用 delta 方向判断谁更优（delta 是 B - A，正数 = B 优）
            if row.delta is not None and isinstance(row.delta, (int, float)):
                # 对 "risks"、"crowding" 等"越大越差"的维度要反转方向
                reverse = dim_id in ("risks", "crowding")
                if row.delta > 0.0001:
                    if not reverse:
                        b_better += 1
                        weighted_b += weight
                    else:
                        a_better += 1
                        weighted_a += weight
                elif row.delta < -0.0001:
                    if not reverse:
                        a_better += 1
                        weighted_a += weight
                    else:
                        b_better += 1
                        weighted_b += weight
                else:
                    tied += 1
            else:
                # 非数值维度：用相对描述长度近似（有描述就不降级，没描述就是 tie）
                if row.relative_description:
                    tied += 1

        # 根据 favor 计算 0~100 分
        if weighted_total > 0:
            a_share = weighted_a / weighted_total
            b_share = weighted_b / weighted_total
        else:
            a_share = b_share = 0.0

        if favor == "A":
            base = int(50 + (a_share - 0.5) * 100)
        elif favor == "B":
            base = int(50 + (b_share - 0.5) * 100)
        else:  # balance：差异越小分越高
            diff = abs(a_share - b_share)
            base = int(100 - diff * 100)
        score = max(0, min(100, base))
        return score, {
            "a_better": a_better, "b_better": b_better, "tied": tied,
            "degraded_rows": degraded_rows, "total": total,
        }

    # ------------------------------------------------------------------
    # 换仓比例计算（部分换仓专用）
    # ------------------------------------------------------------------

    def _compute_partial_ratio(self, m: ComparisonMatrix, pref: UserPreference
                               ) -> tuple[float, list[str]]:
        """确定性计算部分换仓比例（0~1），原因列表用于透明化"""
        reasons: list[str] = []
        # 基准：50%
        ratio = 0.50
        # 叠加：B 优比例
        _, signals = self._score_by_dimensions(m, favor="B")
        if signals["total"] > 0:
            tilt = (signals["b_better"] - signals["a_better"]) / signals["total"]
            ratio += tilt * 0.40  # 极端 tilt=1 时增加 40%，极端 -1 时减少 40%
        # 用户约束
        lo = pref.min_switch_ratio if pref.min_switch_ratio is not None else 0.0
        hi = pref.max_switch_ratio if pref.max_switch_ratio is not None else 1.0
        if lo > 0:
            reasons.append(f"用户硬约束：最小换仓 {lo*100:.0f}%")
        if hi < 1:
            reasons.append(f"用户硬约束：最大换仓 {hi*100:.0f}%")
        ratio = max(lo, min(hi, ratio))
        ratio = round(ratio, 2)
        if ratio < 0.05:
            ratio = 0.0
            reasons.append("计算结果低于 5%，按 0% 处理（实际不换仓）")
        return ratio, reasons

    # ------------------------------------------------------------------
    # 各方案的成立条件与失效条件（构造辅助：都用可验证指标）
    # ------------------------------------------------------------------

    def _build_hold_valid(self, m, pref) -> list[DecisionCondition]:
        """方案1（继续持有）成立条件"""
        conds: list[DecisionCondition] = []
        val = m.get_row("valuation")
        if val and isinstance(val.a.value, dict):
            up = val.a.value.get("upside_potential")
            if up is not None and up >= 0.10:
                conds.append(DecisionCondition(
                    description=f"A 标的阶段4上行空间 >= 10%（当前 {up*100:.1f}%）",
                    indicator="a_upside_potential",
                    threshold=0.10, current_value=round(up, 4),
                    unit="小数", direction="gte", met=True,
                    source="phase4_valuation",
                ))
        # A 的核心风险没有爆发
        risk = m.get_row("risks")
        if risk and not risk.a.degraded:
            conds.append(DecisionCondition(
                description="A 标的已识别风险清单内没有已实质性爆发的事件",
                indicator="a_risk_breakout", threshold=0,
                current_value=0 if risk.a.value else None,
                unit="已爆发项数", direction="lte",
                met=(risk.a.value is not None and len(risk.a.value) >= 0),
                source="user_input",
            ))
        return conds

    def _build_hold_invalid(self, m, pref) -> list[DecisionCondition]:
        """方案1 失效条件：一旦发生，就不该继续持有 A"""
        conds: list[DecisionCondition] = []
        val = m.get_row("valuation")
        if val and isinstance(val.b.value, dict):
            b_up = val.b.value.get("upside_potential")
            a_up = val.a.value.get("upside_potential") if isinstance(val.a.value, dict) else None
            if a_up is not None and b_up is not None and (b_up - a_up) >= 0.20:
                conds.append(DecisionCondition(
                    description=f"B 的上行空间（{b_up*100:.1f}%）比 A（{a_up*100:.1f}%）高 >= 20 个百分点",
                    indicator="b_minus_a_upside",
                    threshold=0.20, current_value=round(b_up - a_up, 4),
                    unit="小数", direction="gte", met=True,
                    source="phase4_valuation",
                ))
        # A 的 IRR 明显为负
        if val and isinstance(val.a.value, dict) and val.a.value.get("upside_potential") is not None:
            up_a = val.a.value["upside_potential"]
            if up_a < -0.10:
                conds.append(DecisionCondition(
                    description=f"A 的目标价低于当前价 >= 10%（当前上行空间 {up_a*100:.1f}%）",
                    indicator="a_downside_10pct",
                    threshold=-0.10, current_value=round(up_a, 4),
                    unit="小数", direction="lte", met=True,
                    source="phase4_valuation",
                ))
        return conds

    def _build_partial_valid(self, m, pref, ratio) -> list[DecisionCondition]:
        conds: list[DecisionCondition] = []
        conds.append(DecisionCondition(
            description=f"计算换仓比例 {ratio*100:.0f}% 在用户约束范围内",
            indicator="partial_ratio_within_bounds",
            threshold=f"[{pref.min_switch_ratio or 0}, {pref.max_switch_ratio or 1}]",
            current_value=ratio, unit="小数", direction="eq",
            met=(pref.min_switch_ratio or 0.0) <= ratio <= (pref.max_switch_ratio or 1.0),
            source="scenario_planner",
        ))
        return conds

    def _build_partial_invalid(self, m, pref, ratio) -> list[DecisionCondition]:
        conds: list[DecisionCondition] = []
        if pref.avoid_short_term_tax:
            conds.append(DecisionCondition(
                description="用户要求规避短期税费，但部分换仓仍需卖出 A 的对应份额",
                indicator="partial_still_taxable",
                threshold=True, current_value=True, unit="bool", direction="eq", met=True,
                source="preference",
            ))
        return conds

    def _build_full_valid(self, m, pref) -> list[DecisionCondition]:
        conds: list[DecisionCondition] = []
        val = m.get_row("valuation")
        if val and isinstance(val.b.value, dict):
            b_up = val.b.value.get("upside_potential")
            if b_up is not None and b_up >= 0.20:
                conds.append(DecisionCondition(
                    description=f"B 的上行空间 >= 20%（当前 {b_up*100:.1f}%）",
                    indicator="b_upside_20pct",
                    threshold=0.20, current_value=round(b_up, 4),
                    unit="小数", direction="gte", met=True,
                    source="phase4_valuation",
                ))
        # B 核心催化至少 1 项已落地或近期可验证
        cat = m.get_row("catalysts")
        if cat and cat.b.value and len(cat.b.value) >= 2:
            conds.append(DecisionCondition(
                description=f"B 的已识别催化 >= 2 项（当前 {len(cat.b.value)} 项）",
                indicator="b_catalysts_count",
                threshold=2, current_value=len(cat.b.value),
                unit="项", direction="gte", met=True,
                source="user_input_or_research",
            ))
        return conds

    def _build_full_invalid(self, m, pref) -> list[DecisionCondition]:
        conds: list[DecisionCondition] = []
        crowd = m.get_row("crowding")
        if crowd and isinstance(crowd.b.value, dict):
            to = crowd.b.value.get("turnover_20d")
            if to is not None and to >= 0.15:  # 15%/天 = 非常拥挤
                conds.append(DecisionCondition(
                    description=f"B 20 日平均换手率 >= 15%（当前 {to*100:.1f}%），交易拥挤",
                    indicator="b_crowding_15pct",
                    threshold=0.15, current_value=round(to, 4),
                    unit="小数/天", direction="gte", met=True,
                    source="market_data",
                ))
        # 价格过热：近 1 月涨幅 >= 30%
        pa = m.get_row("price_action")
        if pa and isinstance(pa.b.value, dict):
            r1m = pa.b.value.get("return_1m")
            if r1m is not None and r1m >= 0.30:
                conds.append(DecisionCondition(
                    description=f"B 近 1 月涨幅 >= 30%（当前 {r1m*100:.1f}%），需警惕追高风险",
                    indicator="b_short_term_overheat",
                    threshold=0.30, current_value=round(r1m, 4),
                    unit="小数", direction="gte", met=True,
                    source="market_data",
                ))
        # ---- 保底 2 条：相对优势反转 / A 持仓约束击穿 ----
        # （否则当数据不满足"过热"两个硬指标时，full_switch 会没有失效条件，
        #  导致独立质量门挂红灯）
        _, signals = self._score_by_dimensions(m, favor="B")
        b_net = signals["b_better"] - signals["a_better"]
        conds.append(DecisionCondition(
            description=f"B 相对于 A 的净优维度数由正转负（当前 {b_net:+d}），"
                        "即相对优势已经反转，全换的大前提不成立",
            indicator="b_net_advantage_reversal",
            threshold=0, current_value=int(b_net),
            unit="个维度", direction="lte", met=bool(b_net <= 0),
            source="comparison_matrix",
        ))
        # A 持仓约束击穿：浮亏一旦超过容忍度或换手率过低，不该继续持有→ 也不该"全换成另一个"（应该先减仓）
        hc = m.get_row("holding_constraints")
        if hc and isinstance(hc.a.value, dict):
            loss_tol = hc.a.value.get("holding_loss_tolerance")
            pos_pct = hc.a.value.get("position_pct")
            cost = hc.a.value.get("cost_per_share")
            cur_price = None
            pa_row = m.get_row("price_action")
            if pa_row and isinstance(pa_row.a.value, dict):
                cur_price = pa_row.a.value.get("current_price")
            if loss_tol is not None and cost and cur_price:
                cur_loss = max(0.0, (float(cost) - float(cur_price)) / max(float(cost), 1e-9))
                conds.append(DecisionCondition(
                    description=f"A 当前浮亏 {cur_loss*100:.1f}% 已超过持仓容忍阈值 {loss_tol*100:.1f}%，"
                                "此时全换到另一个标的属于'在恐慌中换仓'，应先减仓控制风险",
                    indicator="a_loss_tolerance_breach",
                    threshold=float(loss_tol), current_value=round(cur_loss, 4),
                    unit="小数", direction="gte", met=bool(cur_loss >= float(loss_tol)),
                    source="holding_constraints",
                ))
            elif pos_pct is not None and float(pos_pct) >= 0.50:
                # 即便没浮亏，单票仓位 > 50% 也不建议"全换成另一个集中持有"
                conds.append(DecisionCondition(
                    description=f"A 原持仓占比 {float(pos_pct)*100:.1f}% 已过高，"
                                "直接全换为单一 B 标的会让组合集中度风险不变甚至放大，"
                                "应先做分散而非全换",
                    indicator="single_ticker_concentration_risk",
                    threshold=0.50, current_value=float(pos_pct),
                    unit="比例", direction="gte", met=bool(float(pos_pct) >= 0.50),
                    source="holding_constraints",
                ))
        return conds

    def _build_wait_valid(self, m) -> list[DecisionCondition]:
        conds: list[DecisionCondition] = []
        if m.data_gaps:
            conds.append(DecisionCondition(
                description=f"至少补齐 {max(1, len(m.data_gaps)//2)} 项核心数据缺口（当前共 {len(m.data_gaps)} 项）",
                indicator="data_gaps_reduced",
                threshold=max(1, len(m.data_gaps) - max(1, len(m.data_gaps)//2)),
                current_value=len(m.data_gaps),
                unit="项", direction="lte", met=None,
                source="comparison_matrix",
            ))
        # ---- 保底 3 条成立条件（即使无 data_gaps，hold_and_wait 也必须有成立条件）----
        # 1) A/B 净优劣势不明显（否则应该直接选 continue 或 switch）
        _, signals = self._score_by_dimensions(m, favor="B")
        b_net = abs(signals["b_better"] - signals["a_better"])
        completeness = m.overall_completeness or 0.0
        closely_matched = (b_net <= 2) or (completeness <= 0.68)
        conds.append(DecisionCondition(
            description=(f"A/B 相对优势胶着（净差 {b_net} 个维度，"
                         f"完整度 {completeness:.0%}），先观察再决策可避免误判"),
            indicator="ab_closely_matched",
            threshold=(2, 0.68), current_value=[int(b_net), round(completeness, 3)],
            unit="(维度,完整度)", direction="lte", met=bool(closely_matched),
            source="comparison_matrix",
        ))
        # 2) B 的关键领先验证节点尚未到（财报、订单、发布等）
        cat_row = m.get_row("catalysts")
        upcoming_catalysts = 0
        if cat_row and cat_row.b.value is not None:
            upcoming_catalysts = len(cat_row.b.value)
        conds.append(DecisionCondition(
            description=f"B 仍有 {upcoming_catalysts} 项待验证催化，等待其中至少 1 项落地可提高确定性",
            indicator="b_upcoming_catalysts_count",
            threshold=1, current_value=upcoming_catalysts,
            unit="项", direction="gte", met=bool(upcoming_catalysts >= 1),
            source="catalysts",
        ))
        # 3) 当前价格状态不支持立即换仓（B 短期过热 或 A 短期超跌，等回调再换更优）
        pa_row = m.get_row("price_action")
        wait_on_price = False
        if pa_row and isinstance(pa_row.b.value, dict):
            b_short = pa_row.b.value.get("short_term_return")
            if b_short is not None and float(b_short) >= 0.15:
                wait_on_price = True
        if pa_row and isinstance(pa_row.a.value, dict):
            a_short = pa_row.a.value.get("short_term_return")
            if a_short is not None and float(a_short) <= -0.12:
                wait_on_price = True
        conds.append(DecisionCondition(
            description="B 短期过热（>=15%）或 A 短期超跌（<=-12%），等价格回落后换仓成本更优",
            indicator="price_near_unfavorable_extreme",
            threshold="极端价格区域", current_value="等待价格回归中值",
            unit="枚举", direction="gte", met=bool(wait_on_price),
            source="price_action",
        ))
        return conds

    def _build_wait_invalid(self, m) -> list[DecisionCondition]:
        conds: list[DecisionCondition] = []
        # ---- 保底 2 条失效条件（确保 hold_and_wait 不会没有失效条件导致质量门挂红灯）----
        # 1. B 相对优势已明确且充分：此时继续等就是踏空
        _, signals = self._score_by_dimensions(m, favor="B")
        b_net = signals["b_better"] - signals["a_better"]
        completeness = m.overall_completeness or 0.0
        # 净优 >= 3 个维度 且 完整度 >= 70%："等"就没道理了
        clearly_b = (b_net >= 3) and (completeness >= 0.70)
        conds.append(DecisionCondition(
            description=f"B 已明显优于 A（净优 {b_net} 个维度，数据完整度 {completeness:.0%}），"
                        "继续等待会错过换仓窗口",
            indicator="b_advantage_clearly_sufficient",
            threshold=(3, 0.70), current_value=[int(b_net), round(completeness, 3)],
            unit="(维度,完整度)", direction="gte", met=bool(clearly_b),
            source="comparison_matrix",
        ))
        # 2. A 持仓端的硬约束已击穿（止损/锁利/税收硬约束）：此时必须行动，不能等
        hc = m.get_row("holding_constraints")
        holding_triggered = False
        holding_desc = "A 持仓硬约束尚未触发"
        if hc and isinstance(hc.a.value, dict):
            loss_tol = hc.a.value.get("holding_loss_tolerance")
            cost = hc.a.value.get("cost_per_share")
            tax_on_short = hc.a.value.get("tax_on_short_term")
            pa_row = m.get_row("price_action")
            cur_price = None
            if pa_row and isinstance(pa_row.a.value, dict):
                cur_price = pa_row.a.value.get("current_price")
            if loss_tol is not None and cost and cur_price:
                cur_loss = max(0.0, (float(cost) - float(cur_price)) / max(float(cost), 1e-9))
                if cur_loss >= float(loss_tol):
                    holding_triggered = True
                    holding_desc = (f"A 已浮亏 {cur_loss*100:.1f}%，达到"
                                    f"容忍阈值 {float(loss_tol)*100:.1f}%，"
                                    "再等可能超过预设止损线")
            elif tax_on_short is not None and float(tax_on_short) >= 0.20:
                # 短期税高是个说明性信号，但不需要直接判定已触发
                pass
            # 如果 A 的价格状态相对强弱指数继续恶化（<0.8），也提示"再等就亏更多"
            if pa_row and isinstance(pa_row.a.value, dict):
                rs = pa_row.a.value.get("relative_strength")
                if rs is not None and float(rs) <= 0.80:
                    holding_triggered = True
                    holding_desc = (f"A 近月相对强弱 <= 0.80（当前 {float(rs):.2f}），"
                                    "明显弱于市场，继续持有/等待会继续落后")
        conds.append(DecisionCondition(
            description=holding_desc,
            indicator="a_holding_hard_constraint",
            threshold="硬约束未触发", current_value=holding_desc,
            unit="枚举", direction="gte", met=bool(holding_triggered),
            source="holding_constraints",
        ))
        # 关键催化已经落地（此时再等就错失）—— 补充：如果 B 催化为 0 条，说明催化均已兑现
        cat = m.get_row("catalysts")
        if cat and cat.b.value is not None and len(cat.b.value) == 0:
            conds.append(DecisionCondition(
                description="B 已列出的未来催化为 0 条，可能意味着关键预期催化均已发生或无法再预期，"
                            "再等没有新信息支撑",
                indicator="b_catalysts_exhausted",
                threshold=0, current_value=0, unit="条", direction="lte",
                met=True, source="research_input",
            ))
        return conds

    def _build_partial_pacing(self, m, ratio) -> list[PacingStep]:
        """构造部分换仓的分批节奏（3 步默认）"""
        steps = [
            PacingStep(1, 1/3, trigger="首批立即 / 首个工作日",
                       indicator="execution_price",
                       rationale=f"先成交 1/3 × {ratio*100:.0f}% = {ratio/3*100:.1f}% 总仓位，降低择时风险"),
            PacingStep(2, 1/3, trigger="首批后 3~8 个交易日或季报公布后 1 日内",
                       indicator="after_event",
                       rationale="中段看 B 的催化落地节奏再执行"),
            PacingStep(3, 1/3, trigger="中段执行后再观察 10+ 交易日 / 或相对价差达到中性区间",
                       indicator="ab_spread_normalization",
                       rationale="尾段避免两头打脸——要么确认趋势再进，要么放弃"),
        ]
        # 如果总比例很小（<=15%），就不分批
        if ratio <= 0.15:
            return [PacingStep(1, 1.0, trigger="比例很小，一次性成交即可",
                               indicator="one_shot_small_position",
                               rationale="总换仓 <= 15%，拆分意义不大")]
        return steps

    # ------------------------------------------------------------------
    # 推荐方案选择（不是执行！只是建议）
    # ------------------------------------------------------------------

    def _select_recommended(self, scenarios: dict[str, DecisionScenario], pref, warnings
                            ) -> tuple[str, str]:
        """按 score 排序、叠加降级惩罚，给出建议 + 置信度"""
        # 算惩罚后的有效分
        effective: list[tuple[str, int]] = []
        for sid, s in scenarios.items():
            penalty = 0
            if s.degraded:
                penalty += 20
                # 降级原因越多罚越多
                penalty += min(20, len(s.degradation_reasons) * 5)
            effective.append((sid, max(0, s.score - penalty)))
        # 全换/部分/持有 等权比较，没有内置偏好
        effective.sort(key=lambda x: -x[1])
        top_sid = effective[0][0]
        top_score = effective[0][1]
        second_score = effective[1][1] if len(effective) > 1 else 0
        # 置信度：分差大则高
        diff = top_score - second_score
        if diff >= 15 and not scenarios[top_sid].degraded:
            confidence = "高"
        elif diff >= 5:
            confidence = "中"
        else:
            confidence = "低"
        # 保守原则：如果 top 是 full_switch 但 confidence 低，推荐升级为 partial
        if top_sid == "full_switch" and confidence == "低":
            top_sid = "partial_switch"
            warnings.append(
                "【推荐调整】完全换仓方案有效分差 < 15，自动降为部分换仓推荐；"
                "如需全换请人工确认。"
            )
        return top_sid, confidence

    # ------------------------------------------------------------------
    # 监控清单（领先指标）
    # ------------------------------------------------------------------

    def _generate_monitoring_list(self, m: ComparisonMatrix) -> list[MonitoringIndicator]:
        """生成确定性的领先指标监控清单"""
        indicators: list[MonitoringIndicator] = []
        # 1. B 的隐含增长 vs 实际
        ind = m.get_row("implied_growth")
        if ind and isinstance(ind.b.value, dict) and ind.b.value.get("implied_cagr") is not None:
            indicators.append(MonitoringIndicator(
                indicator_id="b_implied_cagr_vs_realized",
                name="B：隐含 CAGR 是否被季度营收印证",
                why_it_matters="当前价格隐含增长若不能兑现，估值将显著回调",
                frequency="每季度财报后",
                current_value=ind.b.value["implied_cagr"],
                unit="%/年 CAGR",
                warn_threshold=ind.b.value["implied_cagr"] * 0.6,  # 实际增长低于隐含 60% 就预警
                direction="below",
                applies_to_scenarios=["partial_switch", "full_switch"],
            ))
        # 2. B 拥挤度是否恶化
        cr = m.get_row("crowding")
        if cr and isinstance(cr.b.value, dict) and cr.b.value.get("turnover_20d") is not None:
            indicators.append(MonitoringIndicator(
                indicator_id="b_20d_turnover_surge",
                name="B：20 日换手率是否突然上冲",
                why_it_matters="换手率翻 2 倍以上常伴随趋势反转或加速赶顶",
                frequency="每周",
                current_value=cr.b.value["turnover_20d"],
                unit="小数/天",
                warn_threshold=cr.b.value["turnover_20d"] * 2,
                direction="above",
                applies_to_scenarios=["partial_switch", "full_switch", "hold_and_wait"],
            ))
        # 3. A 的盈利是否继续达标（继续持有/暂缓）
        rq = m.get_row("revenue_quality")
        if rq and isinstance(rq.a.value, dict) and rq.a.value.get("net_margin") is not None:
            indicators.append(MonitoringIndicator(
                indicator_id="a_net_margin_retention",
                name="A：净利率是否维持在当前水平以上",
                why_it_matters="若 A 净利率快速恶化，即使不换仓也需重新评估持仓",
                frequency="每季度财报后",
                current_value=rq.a.value["net_margin"],
                unit="小数",
                warn_threshold=rq.a.value["net_margin"] * 0.85,
                direction="below",
                applies_to_scenarios=["continue_hold", "hold_and_wait", "partial_switch"],
            ))
        # 4. A vs B 估值差是否走极端
        v = m.get_row("valuation")
        if v and isinstance(v.a.value, dict) and isinstance(v.b.value, dict):
            a_pe = v.a.value.get("pe_ttm")
            b_pe = v.b.value.get("pe_ttm")
            if a_pe and b_pe and a_pe > 0 and b_pe > 0:
                ratio = b_pe / a_pe
                indicators.append(MonitoringIndicator(
                    indicator_id="ab_pe_ratio_extremes",
                    name="A/B 估值（PE TTM）相对比值",
                    why_it_matters="比值 > 2x 或 < 0.5x 时，相对性价比显著偏移，需重估换仓必要性",
                    frequency="每周",
                    current_value=round(ratio, 2),
                    unit="B_PE / A_PE",
                    warn_threshold=(0.5, 2.0),
                    direction="outside_range",
                    applies_to_scenarios=["continue_hold", "partial_switch", "full_switch", "hold_and_wait"],
                ))
        # 5. B 已识别风险是否爆发
        rk = m.get_row("risks")
        if rk and rk.b.value and len(rk.b.value) > 0:
            indicators.append(MonitoringIndicator(
                indicator_id="b_top_risk_items_status",
                name=f"B：已识别 {len(rk.b.value)} 项核心风险的进展",
                why_it_matters="任何一项风险爆发都可能推翻成立条件",
                frequency="每周",
                current_value=len(rk.b.value),
                unit="已识别风险项数",
                warn_threshold=1,
                direction="above",
                applies_to_scenarios=["full_switch", "partial_switch"],
            ))
        return indicators
