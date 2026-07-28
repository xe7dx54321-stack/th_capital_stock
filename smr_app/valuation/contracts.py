"""
估值契约 - 数据结构定义

功能说明：
    定义估值引擎的输入和输出数据结构。
    核心原则：假设与事实明确分栏，每个历史输入有来源和时点。

参数说明：
    ValuationInput - 估值输入（驱动变量、公式、股本、价格等）
    DriverAssumption - 驱动变量假设（名称、值、单位、来源、是否假设）
    ValuationResult - 估值输出（预测、摘要、假设表）

返回值说明：
    纯数据类，不包含计算逻辑

异常处理：
    无
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DriverAssumption:
    """
    单个驱动变量假设

    小白讲解：
        这就像做菜的一个食材——"DCU 出货量 2026 年 30 万颗"。
        is_assumption=True 表示这是假设（不是已确认事实），
        source 记录假设来源（分析师估算/用户指定/系统推断）。
    """
    name: str           # 变量名（如 "dcu_shipment"）
    label: str          # 中文标签（如 "DCU出货量"）
    unit: str           # 单位（如 "万颗"）
    values_by_year: dict  # {2026: 30, 2027: 50, 2028: 80}
    source: str         # 来源（如 "analyst_estimate"）
    is_assumption: bool = True  # 是否为假设（vs 已确认事实）


@dataclass
class ValuationInput:
    """
    估值输入

    小白讲解：
        这是一份完整的"菜谱"——食材（drivers）、做法（formulas）、
        菜量（shares）、定价依据（current_price, terminal_pe）。
        引擎按这份菜谱一步步做菜，最后输出一份完整的估值报告。
    """
    entity_key: str                    # 实体标识（如 "688041.SH"）
    forecast_years: list               # 预测年份列表 [2026, 2027, 2028]
    drivers: list                      # DriverAssumption 列表
    revenue_formula: str               # 收入公式（如 "dcu_shipment * dcu_asp + cpu_revenue"）
    profit_formula: Optional[str] = None  # 利润公式（如 "revenue * (gross_margin - expense_rate) * (1 - tax_rate)"）
    shares_outstanding: Optional[float] = None  # 股本（亿股）
    current_price: Optional[float] = None       # 当前价格（元）
    current_market_cap: Optional[float] = None  # 当前市值（亿元）
    terminal_pe: Optional[float] = None         # 终值 PE
    forecast_horizon_years: int = 3             # 预测年限（用于 IRR 计算）


@dataclass
class ValuationResult:
    """
    估值输出

    小白讲解：
        这是做好的"菜"——包含每一步的计算结果，
        以及最终的摘要（目标价、目标市值、IRR）。
        每个数字都可以从输入和公式独立复算。
    """
    entity_key: str
    projections: dict = field(default_factory=dict)  # {指标: {年份: 值}}
    summary: dict = field(default_factory=dict)       # 摘要（target_price, target_market_cap, irr）
    assumptions_table: list = field(default_factory=list)  # 假设表（用于假设与事实分栏）
    input_snapshot: dict = field(default_factory=dict)  # 输入快照（用于复算）
    warnings: list = field(default_factory=list)  # 警告列表
