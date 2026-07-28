"""
同口径比较矩阵 - 双标的换仓决策基础数据

功能说明：
    为"把 A 换成 B"的决策提供同口径的基础数据。
    核心原则（来自 master plan 阶段 5）：
    - 两标的行情时点差不超过配置阈值
    - 市值、PE、PB、利润等单位一致（全部统一为 亿元、倍、%）
    - 调用阶段 4 的估值制品（ValuationResult），而非重复手算
    - 任一核心数据冲突时相关维度局部降级（marked as degraded）
    - 不把"昂贵/便宜"直接等同于"买入/卖出"（只给出相对描述）

    12 个分析维度：
    1. 生命周期          (lifecycle_stage)
    2. 收入/利润质量      (revenue_profit_quality)
    3. 现金流            (cash_flow)
    4. ROE              (roe)
    5. 估值              (valuation)
    6. 隐含增长          (implied_growth)
    7. 产业位置          (industry_position)
    8. 催化              (catalysts)
    9. 风险              (risks)
    10. 拥挤度           (crowding)
    11. 近期价格状态      (price_action)
    12. 用户持仓约束      (holding_constraints)

参数说明：
    ComparisonInput - 单个标的的输入数据（市场快照+估值结果+行业标签+价格序列）
    ComparisonMatrixBuilder.build(a_input, b_input, common_as_of) - 构建矩阵
    normalize_units(row, target_unit) - 单位统一化工具
    check_temporal_alignment(a_snapshot, b_snapshot, threshold_hours) - 时点对齐检查

返回值说明：
    ComparisonMatrix 数据类，包含：
    - dimensions: dict[维度名] = {A值, B值, 差值, 单位, 数据等级, 是否降级}
    - summary: 单位一致性、时点一致性、数据完整度统计
    - data_gaps: 未解决数据缺口列表
    - warnings: 警告列表

异常处理：
    数据缺失时该维度被标记 degraded，不抛异常
    单位不一致时尝试自动转换，失败则 degraded
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


# ============================================================================
# 数据结构定义
# ============================================================================


@dataclass
class ComparisonInput:
    """
    单个标的的输入数据

    小白讲解：
        这是"一位选手的档案袋"——包含他的市场数据、估值结果、
        行业标签、价格走势、催化事件等。
        把 A 和 B 两个档案袋交给 ComparisonMatrixBuilder，
        就能生成一张同口径的对比成绩单。
    """
    ticker: str                                         # 标的代码（如 "688041.SH"）
    name: str = ""                                      # 公司名（如 "海光信息"）
    # === 市场快照（fundamentals_snapshot + valuation_snapshot）===
    revenue: Optional[float] = None                     # 营业收入（亿元）
    net_income: Optional[float] = None                  # 净利润（亿元）
    gross_margin: Optional[float] = None                # 毛利率（小数，0.55 = 55%）
    net_margin: Optional[float] = None                  # 净利率（小数）
    operating_margin: Optional[float] = None            # 经营利润率（小数）
    roe: Optional[float] = None                         # ROE（小数，0.15 = 15%）
    pe_ttm: Optional[float] = None                      # PE TTM（倍）
    pb: Optional[float] = None                          # PB（倍）
    current_price: Optional[float] = None               # 当前价格（元）
    market_cap: Optional[float] = None                  # 当前市值（亿元）
    shares_outstanding: Optional[float] = None          # 股本（亿股）
    free_cash_flow: Optional[float] = None              # 自由现金流（亿元）
    operating_cash_flow: Optional[float] = None         # 经营现金流（亿元）
    # === 阶段 4 估值制品（ValuationResult 摘要）===
    valuation_target_price: Optional[float] = None      # 阶段4目标价（元）
    valuation_target_market_cap: Optional[float] = None # 阶段4目标市值（亿元）
    valuation_irr: Optional[float] = None               # 阶段4 IRR（小数）
    implied_cagr: Optional[float] = None                # 当前价格隐含 CAGR（小数）
    implied_net_margin: Optional[float] = None          # 当前价格隐含净利率（小数）
    # === 元数据（时点、来源、权威等级）===
    snapshot_as_of: Optional[str] = None                # 快照时点（ISO 字符串）
    valuation_as_of: Optional[str] = None               # 估值时点
    fundamentals_period: Optional[str] = None           # 财务报告期（如 "2025Q4"）
    source_authority_tier: int = 3                      # 权威等级（1=交易所, 2=数据商, 3=聚合）
    # === 行业与生命周期（外部标签，允许缺失）===
    industry: str = ""                                  # 行业（如 "半导体"）
    lifecycle_stage: str = ""                           # 成长期/成熟期/衰退期/导入期
    industry_position: str = ""                         # 龙头/跟随者/细分冠军等
    # === 拥挤度与价格状态（允许缺失）===
    turnover_rate_20d: Optional[float] = None           # 20日平均换手率（小数）
    short_term_return: Optional[float] = None           # 近1个月涨跌幅（小数，0.10 = +10%）
    medium_term_return: Optional[float] = None          # 近3个月涨跌幅
    relative_strength: Optional[float] = None           # 相对强弱（跑赢/跑赢基准百分比，小数）
    # === 催化与风险（文本描述，用于定性维度）===
    catalysts: list[str] = field(default_factory=list)  # 近期催化清单
    risks: list[str] = field(default_factory=list)      # 主要风险清单
    # === 用户持仓约束（只用于 A 标的，即当前持仓方）===
    holding_shares: Optional[float] = None              # 持仓股数（万股）
    holding_cost: Optional[float] = None                # 持仓成本（元）
    holding_position_pct: Optional[float] = None        # 持仓占组合比例（小数，0.30 = 30%）
    holding_loss_tolerance: Optional[float] = None      # 可接受最大亏损（小数）
    tax_on_short_term: Optional[float] = None           # 短期持有税费（小数，如 0.01 = 1%）


@dataclass
class DimensionCell:
    """
    比较矩阵的一个单元格（某标的、某维度的值）

    小白讲解：
        这是"成绩单上的一个格子"。
        value 是分数，unit 是单位，tier 是数据可信度，
        degraded 表示这个格子因为数据缺失/冲突而不可靠。
    """
    value: Any = None                # 数值（或文本）
    unit: str = ""                   # 单位（"亿元"、"%"、"倍"、"文本"等）
    authority_tier: int = 4          # 权威等级（1=官方, 2=数据商, 3=聚合, 4=推断）
    degraded: bool = False           # 是否降级（数据缺失/冲突）
    degradation_reason: str = ""     # 降级原因
    source: str = ""                 # 来源标签


@dataclass
class DimensionRow:
    """
    比较矩阵的一行（一个维度，含 A 和 B）

    小白讲解：
        这是"成绩单的一行"，比如 ROE 这行，
        左边是 A 公司的 ROE，右边是 B 公司的 ROE，
        中间是它们的差值和相对描述。
        note 用来解释这个维度的含义，
        interpretation 只做中性描述，不直接给买卖建议。
    """
    dimension_id: str               # 维度 ID（如 "roe"）
    dimension_label: str            # 维度中文名（如 "ROE"）
    a: DimensionCell = field(default_factory=DimensionCell)
    b: DimensionCell = field(default_factory=DimensionCell)
    delta: Any = None               # 差值（B - A，正向表示 B 更优）
    relative_description: str = ""  # 中性描述（如 "B 的 ROE 比 A 高 5 个百分点"）
    note: str = ""                  # 维度说明
    data_conflict: bool = False     # 是否存在核心数据冲突
    conflict_detail: str = ""       # 冲突详情


@dataclass
class ComparisonMatrix:
    """
    双标的同口径比较矩阵

    小白讲解：
        这是"完整的双人成绩单"。
        rows 是逐行的对比，
        summary 告诉你单位有没有对齐、时点差多少、数据完整度如何，
        data_gaps 列出了哪些数据还没拿到（需要用户补充或后续获取）。
    """
    a_ticker: str
    b_ticker: str
    a_name: str = ""
    b_name: str = ""
    rows: dict[str, DimensionRow] = field(default_factory=dict)
    units_consistent: bool = True               # 单位是否整体一致
    temporal_alignment_hours: float = 0.0       # 两标的快照的时点差（小时）
    temporal_alignment_pass: bool = True        # 时点差是否在阈值内
    overall_completeness: float = 0.0           # 数据完整度（0.0 ~ 1.0）
    degraded_dimension_count: int = 0           # 降级维度数量
    data_gaps: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def get_row(self, dimension_id: str) -> Optional[DimensionRow]:
        """按 ID 获取行"""
        return self.rows.get(dimension_id)

    def all_dimension_ids(self) -> list[str]:
        """返回所有维度 ID 的有序列表"""
        order = [
            "lifecycle", "revenue_quality", "cash_flow", "roe",
            "valuation", "implied_growth", "industry_position",
            "catalysts", "risks", "crowding", "price_action",
            "holding_constraints",
        ]
        return [d for d in order if d in self.rows]


# ============================================================================
# 单位统一化工具
# ============================================================================


# 允许的单位集合与统一目标
_UNIT_NORMALIZATION = {
    "收入类": {"亿元": 1.0, "万元": 1e-4, "元": 1e-8, "百万": 0.01, "亿": 1.0},
    "股价类": {"元": 1.0, "万元": 10000.0},
    "百分比": {"%": 0.01, "倍": None, "小数": 1.0},
    "倍数类": {"倍": 1.0, "x": 1.0, "X": 1.0},
}


def normalize_percentage(raw_value: Optional[float], unit: str) -> tuple[Optional[float], str, bool]:
    """
    百分比单位统一：都转成小数形式（50% → 0.50）

    小白讲解：
        有人说毛利率 50，有人说 0.5，有人说 50%。
        统一成 0.50，这样比较才不会错。
        返回 (转换后值, 标准单位, 是否发生了降级)
    """
    if raw_value is None:
        return None, "%", False
    if unit == "%":
        # 百分号格式，看 abs>1 说明是 50 这种写法
        if abs(raw_value) > 1.5:
            return raw_value / 100.0, "%", False
        # 否则已经是小数形式（0.5），但单位标成了 %，视为用户标错
        return raw_value, "%", False
    # 没有单位或其他情况
    if abs(raw_value) > 1.5:
        return raw_value / 100.0, "%", False
    return raw_value, "%", False


def normalize_currency_yi(raw_value: Optional[float], unit: str) -> tuple[Optional[float], str, bool]:
    """
    货币金额单位统一：都转成"亿元"

    小白讲解：
        有人说收入 1000 万，有人说 0.1 亿。
        统一成亿元，这样 A 和 B 才能直接对比。
    """
    if raw_value is None:
        return None, "亿元", False
    unit_table = _UNIT_NORMALIZATION["收入类"]
    factor = unit_table.get(unit)
    if factor is None:
        # 未知单位，不转但标记降级
        return raw_value, unit, True
    return raw_value * factor, "亿元", False


def normalize_multiplier(raw_value: Optional[float], unit: str) -> tuple[Optional[float], str, bool]:
    """倍数类单位统一（PE、PB 等），都转成"倍" """
    if raw_value is None:
        return None, "倍", False
    if unit in ("倍", "x", "X", ""):
        return raw_value, "倍", False
    return raw_value, unit, True


# ============================================================================
# 时点对齐检查
# ============================================================================


def check_temporal_alignment(
    a_as_of: Optional[str],
    b_as_of: Optional[str],
    threshold_hours: float = 72.0,
) -> tuple[bool, float, str]:
    """
    检查两标的快照时点是否对齐

    小白讲解：
        A 标的是 3 天前的价格，B 标的是今天的价格，
        差了 3 天，超过 72 小时阈值就标记不一致。
        返回 (是否通过, 时点差小时数, 说明)
    """
    if not a_as_of or not b_as_of:
        return False, 0.0, "一方或双方缺失快照时点"

    try:
        a_dt = datetime.fromisoformat(a_as_of.replace("Z", "+00:00"))
        b_dt = datetime.fromisoformat(b_as_of.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return False, 0.0, "时点格式无法解析"

    delta_h = abs((a_dt - b_dt).total_seconds()) / 3600.0
    passed = delta_h <= threshold_hours
    reason = "" if passed else f"时点差 {delta_h:.1f} 小时 超过阈值 {threshold_hours:.0f} 小时"
    return passed, delta_h, reason


# ============================================================================
# 比较矩阵构建器
# ============================================================================


# 12 个维度的元数据（ID → (中文名, 说明)）
DIMENSION_META: dict[str, tuple[str, str]] = {
    "lifecycle": ("生命周期", "公司处于导入期/成长期/成熟期/衰退期，决定增长天花板与波动特征"),
    "revenue_quality": ("收入/利润质量", "收入增速、利润率结构、主营占比，反映盈利持续性"),
    "cash_flow": ("现金流", "经营现金流/自由现金流 vs 净利润，验证盈利真实性和造血能力"),
    "roe": ("ROE", "净资产收益率，衡量资本使用效率"),
    "valuation": ("估值", "当前 PE、PB vs 阶段 4 目标估值，评估昂贵/便宜程度（中性描述）"),
    "implied_growth": ("隐含增长", "当前价格反解的隐含 CAGR / 净利率，衡量市场预期高低"),
    "industry_position": ("产业位置", "产业链位置：上游/中游/下游、龙头/跟随者、议价能力"),
    "catalysts": ("催化", "近期可验证的催化事件（产品、订单、政策、产能等）"),
    "risks": ("风险", "核心风险点（竞争、技术、客户、监管、周期等）"),
    "crowding": ("拥挤度", "换手率、机构持仓集中度，衡量交易拥挤风险"),
    "price_action": ("近期价格状态", "近 1/3 月涨跌、相对强弱、动量或反转信号"),
    "holding_constraints": ("持仓约束", "持仓占比、成本、亏损容忍、短期税费，仅用于 A 标的"),
}


class ComparisonMatrixBuilder:
    """
    同口径比较矩阵构建器

    小白讲解：
        这是"裁判"——拿 A 和 B 两位选手的档案，
        按 12 个项目逐一打分，生成一份中性的对比成绩单。
        裁判**不会**直接说"换不换"，只说事实：
        A 的 ROE 是 X，B 的 ROE 是 Y，B 比 A 高 Z。
    """

    def __init__(self, *, threshold_hours: float = 72.0):
        """
        参数:
            threshold_hours: 两标的快照时点差允许阈值（小时），默认 72h = 3 天
        """
        self.threshold_hours = threshold_hours

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------

    def build(
        self,
        a_input: ComparisonInput,
        b_input: ComparisonInput,
        *,
        common_as_of: Optional[str] = None,
    ) -> ComparisonMatrix:
        """
        构建双标的同口径比较矩阵

        参数:
            a_input: 被换出标的（当前持仓）的输入
            b_input: 被换入标的（候选持仓）的输入
            common_as_of: 本次决策的参考时点，None 时使用较新的一方

        返回:
            ComparisonMatrix 对象
        """
        matrix = ComparisonMatrix(
            a_ticker=a_input.ticker,
            b_ticker=b_input.ticker,
            a_name=a_input.name,
            b_name=b_input.name,
        )
        warnings: list[str] = []

        # === 时点对齐检查 ===
        ref_a = common_as_of or a_input.snapshot_as_of
        ref_b = common_as_of or b_input.snapshot_as_of
        aligned, delta_h, align_reason = check_temporal_alignment(
            ref_a, ref_b, self.threshold_hours,
        )
        matrix.temporal_alignment_pass = aligned
        matrix.temporal_alignment_hours = delta_h
        if not aligned:
            warnings.append(f"时点对齐未通过：{align_reason}；相关维度（估值/价格状态）将降级")

        # === 逐行构建 12 维度 ===
        self._build_lifecycle_row(matrix, a_input, b_input, aligned, warnings)
        self._build_revenue_quality_row(matrix, a_input, b_input, aligned, warnings)
        self._build_cash_flow_row(matrix, a_input, b_input, aligned, warnings)
        self._build_roe_row(matrix, a_input, b_input, aligned, warnings)
        self._build_valuation_row(matrix, a_input, b_input, aligned, warnings)
        self._build_implied_growth_row(matrix, a_input, b_input, aligned, warnings)
        self._build_industry_position_row(matrix, a_input, b_input, warnings)
        self._build_catalysts_row(matrix, a_input, b_input, warnings)
        self._build_risks_row(matrix, a_input, b_input, warnings)
        self._build_crowding_row(matrix, a_input, b_input, aligned, warnings)
        self._build_price_action_row(matrix, a_input, b_input, aligned, warnings)
        self._build_holding_constraints_row(matrix, a_input, warnings)

        # === 统计 ===
        matrix.warnings = warnings
        degraded_cnt = 0
        total_cells = 0
        filled_cells = 0
        for row in matrix.rows.values():
            for cell in (row.a, row.b):
                total_cells += 1
                if cell.degraded:
                    degraded_cnt += 1
                if cell.value is not None and not cell.degraded:
                    filled_cells += 1
            if row.a.degraded or row.b.degraded:
                degraded_cnt  # 保留占位（实际上面的循环已经统计了单元格级 degraded）
        matrix.degraded_dimension_count = sum(
            1 for r in matrix.rows.values() if r.a.degraded or r.b.degraded
        )
        matrix.overall_completeness = (
            filled_cells / total_cells if total_cells > 0 else 0.0
        )

        # === 单位一致性（PE、PB、利润、市值等都应是一致单位）===
        matrix.units_consistent = self._check_units_consistency(matrix)
        if not matrix.units_consistent:
            warnings.append("检测到单位不一致：比较结果仅用于参考，相关维度已标记降级")

        # === 数据缺口 ===
        matrix.data_gaps = self._collect_data_gaps(matrix, a_input, b_input)

        return matrix

    # ------------------------------------------------------------------
    # 12 个维度的构建方法（每个维度独立函数，逻辑清晰）
    # ------------------------------------------------------------------

    def _make_row(self, dim_id: str) -> DimensionRow:
        label, note = DIMENSION_META[dim_id]
        return DimensionRow(dimension_id=dim_id, dimension_label=label, note=note)

    @staticmethod
    def _cell(value, unit, tier, source="", degraded=False, reason="") -> DimensionCell:
        return DimensionCell(
            value=value, unit=unit, authority_tier=tier,
            degraded=degraded, degradation_reason=reason, source=source,
        )

    # ---- 1. 生命周期 ----
    def _build_lifecycle_row(self, matrix, a, b, aligned, warnings):
        row = self._make_row("lifecycle")
        row.a = self._cell(a.lifecycle_stage or None, "文本",
                           tier=4, source="industry_tag",
                           degraded=(not a.lifecycle_stage),
                           reason="" if a.lifecycle_stage else "生命周期标签缺失")
        row.b = self._cell(b.lifecycle_stage or None, "文本",
                           tier=4, source="industry_tag",
                           degraded=(not b.lifecycle_stage),
                           reason="" if b.lifecycle_stage else "生命周期标签缺失")
        if row.a.value and row.b.value:
            row.delta = None
            row.relative_description = (
                f"{a.name or a.ticker} 处于 {row.a.value}；"
                f"{b.name or b.ticker} 处于 {row.b.value}"
            )
        matrix.rows["lifecycle"] = row

    # ---- 2. 收入/利润质量 ----
    def _build_revenue_quality_row(self, matrix, a, b, aligned, warnings):
        row = self._make_row("revenue_quality")
        # A
        a_nm, a_unit, a_deg = normalize_percentage(a.net_margin, "%")
        a_gm, _, _ = normalize_percentage(a.gross_margin, "%")
        a_rev, a_rev_unit, a_rev_deg = normalize_currency_yi(a.revenue, "亿元")
        a_degraded = a_deg or a_rev_deg or (a_nm is None and a_gm is None)
        row.a = self._cell(
            {"revenue": a_rev, "net_margin": a_nm, "gross_margin": a_gm},
            unit="亿元/%", tier=min(a.source_authority_tier + 1, 4),
            source="fundamentals_snapshot", degraded=a_degraded,
            reason="收入或利润率缺失" if a_degraded else "",
        )
        # B
        b_nm, _, b_deg = normalize_percentage(b.net_margin, "%")
        b_gm, _, _ = normalize_percentage(b.gross_margin, "%")
        b_rev, _, b_rev_deg = normalize_currency_yi(b.revenue, "亿元")
        b_degraded = b_deg or b_rev_deg or (b_nm is None and b_gm is None)
        row.b = self._cell(
            {"revenue": b_rev, "net_margin": b_nm, "gross_margin": b_gm},
            unit="亿元/%", tier=min(b.source_authority_tier + 1, 4),
            source="fundamentals_snapshot", degraded=b_degraded,
            reason="收入或利润率缺失" if b_degraded else "",
        )
        # 相对描述（只说差，不做买卖判断）
        if a_nm is not None and b_nm is not None:
            diff_pct = (b_nm - a_nm) * 100.0  # 转百分点显示
            direction = "高" if diff_pct >= 0 else "低"
            row.delta = round(diff_pct, 2)
            row.relative_description = (
                f"净利率：{b.name or b.ticker} 比 {a.name or a.ticker} "
                f"{direction} {abs(diff_pct):.2f} 个百分点"
            )
        elif a_rev is not None and b_rev is not None:
            row.relative_description = (
                f"收入规模：{a.name or a.ticker} {a_rev:.1f} 亿元 vs "
                f"{b.name or b.ticker} {b_rev:.1f} 亿元"
            )
        matrix.rows["revenue_quality"] = row

    # ---- 3. 现金流 ----
    def _build_cash_flow_row(self, matrix, a, b, aligned, warnings):
        row = self._make_row("cash_flow")
        a_ocf, _, a_d1 = normalize_currency_yi(a.operating_cash_flow, "亿元")
        a_fcf, _, a_d2 = normalize_currency_yi(a.free_cash_flow, "亿元")
        a_ni, _, _ = normalize_currency_yi(a.net_income, "亿元")
        # 现金流质量 = 经营现金流 / 净利润（>1 说明现金含量高）
        a_ratio = (a_ocf / a_ni) if (a_ocf is not None and a_ni and a_ni != 0) else None
        a_deg = (a_ocf is None and a_fcf is None)
        row.a = self._cell(
            {"operating_cf": a_ocf, "free_cf": a_fcf, "cf_to_ni": a_ratio},
            unit="亿元/倍", tier=min(a.source_authority_tier + 1, 4),
            source="fundamentals_snapshot", degraded=a_deg or a_d1 or a_d2,
            reason="经营/自由现金流数据缺失" if a_deg else "",
        )
        b_ocf, _, b_d1 = normalize_currency_yi(b.operating_cash_flow, "亿元")
        b_fcf, _, b_d2 = normalize_currency_yi(b.free_cash_flow, "亿元")
        b_ni, _, _ = normalize_currency_yi(b.net_income, "亿元")
        b_ratio = (b_ocf / b_ni) if (b_ocf is not None and b_ni and b_ni != 0) else None
        b_deg = (b_ocf is None and b_fcf is None)
        row.b = self._cell(
            {"operating_cf": b_ocf, "free_cf": b_fcf, "cf_to_ni": b_ratio},
            unit="亿元/倍", tier=min(b.source_authority_tier + 1, 4),
            source="fundamentals_snapshot", degraded=b_deg or b_d1 or b_d2,
            reason="经营/自由现金流数据缺失" if b_deg else "",
        )
        if a_ratio is not None and b_ratio is not None:
            diff = round(b_ratio - a_ratio, 3)
            direction = "高" if diff >= 0 else "低"
            row.delta = diff
            row.relative_description = (
                f"现金含量（经营CF/净利）：{b.name or b.ticker} 比 {a.name or a.ticker} "
                f"{direction} {abs(diff):.3f} 倍"
            )
        matrix.rows["cash_flow"] = row

    # ---- 4. ROE ----
    def _build_roe_row(self, matrix, a, b, aligned, warnings):
        row = self._make_row("roe")
        a_roe, _, a_deg = normalize_percentage(a.roe, "%")
        row.a = self._cell(a_roe, "%", tier=min(a.source_authority_tier, 4),
                           source="fundamentals_snapshot",
                           degraded=a_deg or a_roe is None,
                           reason="ROE 缺失" if a_roe is None else "")
        b_roe, _, b_deg = normalize_percentage(b.roe, "%")
        row.b = self._cell(b_roe, "%", tier=min(b.source_authority_tier, 4),
                           source="fundamentals_snapshot",
                           degraded=b_deg or b_roe is None,
                           reason="ROE 缺失" if b_roe is None else "")
        if a_roe is not None and b_roe is not None:
            diff = round((b_roe - a_roe) * 100, 2)  # 转百分点
            direction = "高" if diff >= 0 else "低"
            row.delta = diff
            row.relative_description = (
                f"ROE：{b.name or b.ticker} 比 {a.name or a.ticker} "
                f"{direction} {abs(diff):.2f} 个百分点"
            )
        matrix.rows["roe"] = row

    # ---- 5. 估值 ----
    def _build_valuation_row(self, matrix, a, b, aligned, warnings):
        row = self._make_row("valuation")
        a_pe, _, a_d1 = normalize_multiplier(a.pe_ttm, "倍")
        a_pb, _, a_d2 = normalize_multiplier(a.pb, "倍")
        a_mcap, _, a_d3 = normalize_currency_yi(a.market_cap, "亿元")
        # 阶段 4 估值制品（关键复用！不重复手算）
        a_tp = a.valuation_target_price
        a_upside = None
        if a_tp is not None and a.current_price and a.current_price > 0:
            a_upside = (a_tp / a.current_price) - 1.0  # 小数，0.2 = +20%
        a_deg = a_d1 or a_d2 or a_d3 or ((a_pe is None) and (a_mcap is None))
        if not aligned:
            a_deg = True
        row.a = self._cell(
            {"pe_ttm": a_pe, "pb": a_pb, "market_cap": a_mcap,
             "target_price": a_tp, "upside_potential": a_upside},
            unit="倍/亿元/元",
            tier=min(a.source_authority_tier, 4),
            source="valuation_snapshot + phase4_valuation",
            degraded=a_deg,
            reason="时点未对齐" if not aligned else ("PE/PB/市值 缺失" if a_deg and aligned else ""),
        )
        b_pe, _, b_d1 = normalize_multiplier(b.pe_ttm, "倍")
        b_pb, _, b_d2 = normalize_multiplier(b.pb, "倍")
        b_mcap, _, b_d3 = normalize_currency_yi(b.market_cap, "亿元")
        b_tp = b.valuation_target_price
        b_upside = None
        if b_tp is not None and b.current_price and b.current_price > 0:
            b_upside = (b_tp / b.current_price) - 1.0
        b_deg = b_d1 or b_d2 or b_d3 or ((b_pe is None) and (b_mcap is None))
        if not aligned:
            b_deg = True
        row.b = self._cell(
            {"pe_ttm": b_pe, "pb": b_pb, "market_cap": b_mcap,
             "target_price": b_tp, "upside_potential": b_upside},
            unit="倍/亿元/元",
            tier=min(b.source_authority_tier, 4),
            source="valuation_snapshot + phase4_valuation",
            degraded=b_deg,
            reason="时点未对齐" if not aligned else ("PE/PB/市值 缺失" if b_deg and aligned else ""),
        )
        # 相对描述（**禁止**直接说"更便宜=应该买入"）
        descs = []
        if a_pe and b_pe:
            if b_pe < a_pe:
                descs.append(f"当前 PE：{b.name or b.ticker}（{b_pe:.1f}倍）低于 {a.name or a.ticker}（{a_pe:.1f}倍）")
            else:
                descs.append(f"当前 PE：{b.name or b.ticker}（{b_pe:.1f}倍）高于 {a.name or a.ticker}（{a_pe:.1f}倍）")
        if a_upside is not None and b_upside is not None:
            if b_upside > a_upside:
                descs.append(
                    f"阶段4 上行空间：{b.name or b.ticker}（{b_upside*100:.1f}%）"
                    f" 高于 {a.name or a.ticker}（{a_upside*100:.1f}%）"
                )
            else:
                descs.append(
                    f"阶段4 上行空间：{b.name or b.ticker}（{b_upside*100:.1f}%）"
                    f" 低于 {a.name or a.ticker}（{a_upside*100:.1f}%）"
                )
        if descs:
            row.relative_description = "；".join(descs)
            # 附加：重要提醒——**不把昂贵/便宜直接等同于买卖信号**
            row.note = (
                row.note + " 【注意】估值高低不直接等同于买入/卖出信号，"
                "需结合生命周期、产业位置、催化与风险综合判断。"
            )
        matrix.rows["valuation"] = row

    # ---- 6. 隐含增长 ----
    def _build_implied_growth_row(self, matrix, a, b, aligned, warnings):
        row = self._make_row("implied_growth")
        a_cagr, _, a_deg = normalize_percentage(a.implied_cagr, "%")
        a_im, _, a_deg2 = normalize_percentage(a.implied_net_margin, "%")
        a_tier = min(a.source_authority_tier + 1, 4) if a.implied_cagr else 4
        row.a = self._cell(
            {"implied_cagr": a_cagr, "implied_net_margin": a_im},
            unit="%", tier=a_tier, source="phase4_reverse_implied",
            degraded=(a_cagr is None and a_im is None) or a_deg or a_deg2 or not aligned,
            reason="隐含增长来自阶段4反解，缺失则降级；时点未对齐则降级"
            if (a_cagr is None and a_im is None) or not aligned else "",
        )
        b_cagr, _, b_deg = normalize_percentage(b.implied_cagr, "%")
        b_im, _, b_deg2 = normalize_percentage(b.implied_net_margin, "%")
        b_tier = min(b.source_authority_tier + 1, 4) if b.implied_cagr else 4
        row.b = self._cell(
            {"implied_cagr": b_cagr, "implied_net_margin": b_im},
            unit="%", tier=b_tier, source="phase4_reverse_implied",
            degraded=(b_cagr is None and b_im is None) or b_deg or b_deg2 or not aligned,
            reason="隐含增长来自阶段4反解，缺失则降级；时点未对齐则降级"
            if (b_cagr is None and b_im is None) or not aligned else "",
        )
        if a_cagr is not None and b_cagr is not None:
            diff = round((b_cagr - a_cagr) * 100, 2)  # 百分点
            direction = "高" if diff >= 0 else "低"
            row.delta = diff
            row.relative_description = (
                f"当前价格隐含 CAGR：{b.name or b.ticker} 比 {a.name or a.ticker} "
                f"{direction} {abs(diff):.2f} 个百分点（差值越大表示市场对 B 的增长预期更高）"
            )
        matrix.rows["implied_growth"] = row

    # ---- 7. 产业位置 ----
    def _build_industry_position_row(self, matrix, a, b, warnings):
        row = self._make_row("industry_position")
        row.a = self._cell(
            {"industry": a.industry, "position": a.industry_position} if a.industry else None,
            unit="文本", tier=4, source="industry_tag",
            degraded=not (a.industry or a.industry_position),
            reason="行业/产业位置标签缺失" if not (a.industry or a.industry_position) else "",
        )
        row.b = self._cell(
            {"industry": b.industry, "position": b.industry_position} if b.industry else None,
            unit="文本", tier=4, source="industry_tag",
            degraded=not (b.industry or b.industry_position),
            reason="行业/产业位置标签缺失" if not (b.industry or b.industry_position) else "",
        )
        if a.industry and b.industry:
            row.relative_description = (
                f"{a.name or a.ticker}（{a.industry} - {a.industry_position or '未标注'}）vs "
                f"{b.name or b.ticker}（{b.industry} - {b.industry_position or '未标注'}）"
            )
        matrix.rows["industry_position"] = row

    # ---- 8. 催化 ----
    def _build_catalysts_row(self, matrix, a, b, warnings):
        row = self._make_row("catalysts")
        row.a = self._cell(
            list(a.catalysts) if a.catalysts else None,
            unit="文本列表", tier=4, source="user_input_or_research",
            degraded=not a.catalysts,
            reason="未输入近期催化事件" if not a.catalysts else "",
        )
        row.b = self._cell(
            list(b.catalysts) if b.catalysts else None,
            unit="文本列表", tier=4, source="user_input_or_research",
            degraded=not b.catalysts,
            reason="未输入近期催化事件" if not b.catalysts else "",
        )
        a_cnt = len(a.catalysts or [])
        b_cnt = len(b.catalysts or [])
        row.relative_description = f"催化数量：{a.name or a.ticker} {a_cnt} 项 vs {b.name or b.ticker} {b_cnt} 项"
        matrix.rows["catalysts"] = row

    # ---- 9. 风险 ----
    def _build_risks_row(self, matrix, a, b, warnings):
        row = self._make_row("risks")
        row.a = self._cell(
            list(a.risks) if a.risks else None, unit="文本列表", tier=4,
            source="user_input_or_research",
            degraded=not a.risks, reason="未输入主要风险" if not a.risks else "",
        )
        row.b = self._cell(
            list(b.risks) if b.risks else None, unit="文本列表", tier=4,
            source="user_input_or_research",
            degraded=not b.risks, reason="未输入主要风险" if not b.risks else "",
        )
        a_cnt = len(a.risks or [])
        b_cnt = len(b.risks or [])
        row.relative_description = f"风险数量：{a.name or a.ticker} {a_cnt} 项 vs {b.name or b.ticker} {b_cnt} 项"
        matrix.rows["risks"] = row

    # ---- 10. 拥挤度 ----
    def _build_crowding_row(self, matrix, a, b, aligned, warnings):
        row = self._make_row("crowding")
        a_to, _, a_deg = normalize_percentage(a.turnover_rate_20d, "%")
        row.a = self._cell(
            {"turnover_20d": a_to}, unit="%",
            tier=min(a.source_authority_tier, 4),
            source="market_data", degraded=a_deg or a_to is None or not aligned,
            reason="20日换手率缺失 / 时点未对齐" if (a_to is None or not aligned) else "",
        )
        b_to, _, b_deg = normalize_percentage(b.turnover_rate_20d, "%")
        row.b = self._cell(
            {"turnover_20d": b_to}, unit="%",
            tier=min(b.source_authority_tier, 4),
            source="market_data", degraded=b_deg or b_to is None or not aligned,
            reason="20日换手率缺失 / 时点未对齐" if (b_to is None or not aligned) else "",
        )
        if a_to is not None and b_to is not None:
            diff = round((b_to - a_to) * 100, 2)  # 百分点
            direction = "高" if diff >= 0 else "低"
            hint = "（高换手率可能暗示交易更拥挤）" if diff > 0 else "（低换手率可能暗示交易更清淡）"
            row.delta = diff
            row.relative_description = (
                f"20日换手率：{b.name or b.ticker} 比 {a.name or a.ticker} "
                f"{direction} {abs(diff):.2f} 个百分点 {hint}"
            )
        matrix.rows["crowding"] = row

    # ---- 11. 近期价格状态 ----
    def _build_price_action_row(self, matrix, a, b, aligned, warnings):
        row = self._make_row("price_action")
        a_1m, _, _ = normalize_percentage(a.short_term_return, "%")
        a_3m, _, _ = normalize_percentage(a.medium_term_return, "%")
        a_rs, _, _ = normalize_percentage(a.relative_strength, "%")
        row.a = self._cell(
            {"return_1m": a_1m, "return_3m": a_3m, "relative_strength": a_rs},
            unit="%", tier=min(a.source_authority_tier, 4),
            source="market_price_history",
            degraded=(a_1m is None and a_3m is None) or not aligned,
            reason="近1月/3月收益缺失 / 时点未对齐"
            if (a_1m is None and a_3m is None) or not aligned else "",
        )
        b_1m, _, _ = normalize_percentage(b.short_term_return, "%")
        b_3m, _, _ = normalize_percentage(b.medium_term_return, "%")
        b_rs, _, _ = normalize_percentage(b.relative_strength, "%")
        row.b = self._cell(
            {"return_1m": b_1m, "return_3m": b_3m, "relative_strength": b_rs},
            unit="%", tier=min(b.source_authority_tier, 4),
            source="market_price_history",
            degraded=(b_1m is None and b_3m is None) or not aligned,
            reason="近1月/3月收益缺失 / 时点未对齐"
            if (b_1m is None and b_3m is None) or not aligned else "",
        )
        if a_1m is not None and b_1m is not None:
            diff = round((b_1m - a_1m) * 100, 2)
            direction = "强" if diff >= 0 else "弱"
            row.delta = diff
            row.relative_description = (
                f"近 1 月涨跌幅：{b.name or b.ticker} 相对 {a.name or a.ticker} "
                f"{direction} {abs(diff):.2f} 个百分点"
            )
        matrix.rows["price_action"] = row

    # ---- 12. 持仓约束（只对 A 有意义，B 留空）----
    def _build_holding_constraints_row(self, matrix, a, warnings):
        row = self._make_row("holding_constraints")
        # 【注意】holding_cost 是"每股成本"（元/股），属于股价类小金额，
        # 不要走 normalize_currency_yi（收入类 1 元 = 1e-8 亿元，会得到 5.5e-7 这种科学计数法）。
        h_cost = a.holding_cost  # 直接保留元/股原值
        h_pos, _, _ = normalize_percentage(a.holding_position_pct, "%")
        h_loss, _, _ = normalize_percentage(a.holding_loss_tolerance, "%")
        has_any = any(v is not None for v in [
            a.holding_shares, a.holding_cost, a.holding_position_pct,
            a.holding_loss_tolerance, a.tax_on_short_term,
        ])
        row.a = self._cell(
            {
                "shares_wan": a.holding_shares,           # 万股
                "cost_per_share": h_cost,                 # 元/股（直接原值，不做亿元换算）
                "position_pct": h_pos,                    # 小数（0.30 = 30%）
                "loss_tolerance": h_loss,                 # 小数
                "short_term_tax": a.tax_on_short_term,    # 小数
            } if has_any else None,
            unit="万股/元/%", tier=1, source="user_holding",
            degraded=not has_any,
            reason="未输入 A 标的持仓信息，换仓成本/冲击无法评估" if not has_any else "",
        )
        # B 标的没有"持仓约束"，直接 None 但不降级
        row.b = DimensionCell(value=None, unit="N/A", authority_tier=4,
                              degraded=False, source="not_applicable",
                              degradation_reason="B 标的为候选方，不适用持仓约束")
        if has_any:
            pos_str = f"{h_pos*100:.1f}%" if h_pos is not None else "未提供"
            cost_str = f"{h_cost:.2f}元/股" if h_cost is not None else "未提供"
            row.relative_description = (
                f"仅适用于 {a.name or a.ticker}（当前持仓）："
                f"持仓占比 {pos_str}，成本 {cost_str}"
            )
        matrix.rows["holding_constraints"] = row

    # ------------------------------------------------------------------
    # 辅助：单位一致性、数据缺口
    # ------------------------------------------------------------------

    @staticmethod
    def _check_units_consistency(matrix: ComparisonMatrix) -> bool:
        """检查对比行 A 和 B 的 unit 是否一致（除了 holding_constraints 特殊）"""
        for dim_id, row in matrix.rows.items():
            if dim_id == "holding_constraints":
                continue
            if row.a.unit and row.b.unit and row.a.unit != row.b.unit:
                # 若是组合单位（"亿元/%"/"亿元/倍"），容忍字符串不同
                if "/" not in row.a.unit or "/" not in row.b.unit:
                    return False
        return True

    @staticmethod
    def _collect_data_gaps(matrix: ComparisonMatrix,
                           a: ComparisonInput,
                           b: ComparisonInput) -> list[str]:
        """收集未解决数据缺口（用于决策备忘录的"需要补充信息"清单）"""
        gaps: list[str] = []
        for dim_id, row in matrix.rows.items():
            label = row.dimension_label
            if row.a.degraded and dim_id != "holding_constraints":
                gaps.append(f"{a.name or a.ticker} 的【{label}】数据缺失或降级：{row.a.degradation_reason or '原因未详'}")
            if row.b.degraded:
                gaps.append(f"{b.name or b.ticker} 的【{label}】数据缺失或降级：{row.b.degradation_reason or '原因未详'}")
        # 阶段 4 估值制品是否缺失（关键数据缺口）
        if a.valuation_target_price is None and a.valuation_target_market_cap is None:
            gaps.append(f"{a.name or a.ticker} 尚未运行阶段 4 经营驱动估值，目标价/市值空白")
        if b.valuation_target_price is None and b.valuation_target_market_cap is None:
            gaps.append(f"{b.name or b.ticker} 尚未运行阶段 4 经营驱动估值，目标价/市值空白")
        return gaps
