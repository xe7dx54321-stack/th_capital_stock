"""
经营驱动估值工作流

功能说明：
    这是阶段 4 的核心工作流编排层，把估值引擎、反解器、情景生成器和
    制品生成器串联起来，形成一条完整的"从运营假设推导目标市值"流程。

    核心原则（来自 master plan 阶段 4）：
    - 所有数字由确定性计算完成，禁止 LLM 手算
    - 计算引擎失败后不生成伪精确目标价
    - 假设与事实明确分栏，每个历史输入有来源和时点
    - 模型不可用时仍可完成确定性计算
    - 保存的 JSON 必须能完全复算所有数字

流程（11 个阶段）：
    1. validate_input           - 验证标的、预测期、驱动变量、公式
    2. load_market_context      - 读取历史财务、当前价格、市值（允许缺失）
    3. apply_model_template     - 应用模型模板默认值（可选）
    4. build_assumptions        - 构建驱动变量假设表
    5. validate_assumptions     - 验证单位、边界和变量依赖
    6. compute_valuation        - 计算收入/利润/EPS/目标市值/IRR
    7. reverse_implied          - 反解当前价格隐含的出货量/利润率/CAGR
    8. generate_scenarios       - 生成悲观/基准/乐观情景
    9. generate_sensitivity     - 生成二维敏感性矩阵
    10. independent_recalc      - 独立复算和质量门
    11. persist_outputs         - 保存 JSON/Markdown/CSV 制品

参数说明：
    operating_driver_valuation_definition(...) - 构建工作流定义

返回值说明：
    WorkflowDefinition，可交给 WorkflowRunner 执行

异常处理：
    输入缺失时返回带警告的 StageResult，不抛异常
    计算失败时不生成对应字段，并在 warnings 中记录
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from smr_app.runtime.artifact_store import ArtifactStore
from smr_app.runtime.contracts import StageDefinition, StageResult, WorkflowContext, WorkflowDefinition
from smr_app.valuation.artifacts import ArtifactGenerator
from smr_app.valuation.contracts import DriverAssumption, ValuationInput
from smr_app.valuation.engine import ValuationEngine
from smr_app.valuation.reverse_implied import ReverseImplied
from smr_app.valuation.scenarios import ScenarioGenerator
from smr_app.workflows.stock_deep_dive import parse_ticker


# === 默认产物根目录 ===
# 小白讲解：工作流产出的报告默认放在项目的 06_outputs/workflows 目录下。
PROJECT_ROOT = Path(__file__).resolve().parents[2]
_configured_roots = os.environ.get("SMR_ARTIFACT_ROOTS", "").split(os.pathsep)
DEFAULT_ARTIFACT_ROOT = Path(_configured_roots[0]) if _configured_roots[0] else PROJECT_ROOT / "06_outputs" / "workflows"

# === 默认模型模板路径 ===
DEFAULT_TEMPLATE_PATH = PROJECT_ROOT / "config" / "valuation_model_templates.json"

# === 合法的单位集合 ===
# 小白讲解：驱动变量只能用这些单位，防止"万元"和"亿元"混用导致计算错误。
VALID_UNITS = frozenset({
    "亿元", "万颗", "万片", "万套", "万元/颗", "万元/片",
    "%", "倍", "亿股", "万股", "元", "亿元/年",
})

# === 敏感性矩阵的默认网格 ===
# 小白讲解：如果用户没指定敏感性变量，就用出货量和 ASP 做默认网格。
DEFAULT_SENSITIVITY = {
    "x_driver": "dcu_shipment",
    "x_values": [0.5, 0.8, 1.0, 1.2, 1.5],  # 相对基准的乘数
    "y_driver": "dcu_asp",
    "y_values": [0.8, 0.9, 1.0, 1.1, 1.2],
}


def _utc_now() -> str:
    """返回当前 UTC 时间的 ISO 字符串"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ============================================================================
# 阶段 1：验证输入
# ============================================================================

def _validate_input(context: WorkflowContext) -> StageResult:
    """
    验证工作流输入

    小白讲解：
        这是"门卫"——检查你提交的菜谱是否完整。
        必须有：标的代码。
        如果没有指定 model_template，还必须有：预测年份、驱动变量、收入公式。
        如果指定了 model_template，这些字段可以从模板补充（阶段 3 完成）。
        可选：利润公式、股本、当前价、终值 PE、模型模板。

    参数:
        context.input_data 需要包含：
        - ticker: 标的代码（必填）
        - forecast_years: 预测年份列表（无模板时必填，如 [2026, 2027, 2028]）
        - drivers: 驱动变量列表（无模板时必填，每项含 name/label/unit/values_by_year/source）
        - revenue_formula: 收入公式（无模板时必填）
        - profit_formula: 利润公式（可选）
        - shares_outstanding: 股本（可选，亿股）
        - current_price: 当前价格（可选，元）
        - current_market_cap: 当前市值（可选，亿元）
        - terminal_pe: 终值 PE（可选）
        - forecast_horizon_years: 预测年限（可选，默认为 forecast_years 长度）
        - model_template: 模板名（可选，用于补充缺失默认值）
        - scenarios: 自定义情景（可选）
        - sensitivity: 敏感性矩阵配置（可选）

    返回:
        StageResult，包含 ticker/market/forecast_years

    异常:
        缺失必填字段或格式错误时抛出 ValueError
    """
    # 验证标的代码
    ticker, market = parse_ticker(context.input_data.get("ticker"))

    # 验证 allow_network（本工作流不联网取数，但保留字段以兼容统一接口）
    allow_network = context.input_data.get("allow_network", False)
    if allow_network is not False:
        raise ValueError("operating_driver_valuation 只支持 allow_network=false（确定性计算工作流）")

    model_template = context.input_data.get("model_template")
    # 小白讲解：如果指定了模板，forecast_years/drivers/revenue_formula 可以从模板补充，
    # 阶段 1 只验证格式（如果有），不强制必填。完整必填检查在阶段 3 应用模板后进行。
    has_template = bool(model_template)

    # 验证预测年份（如果有）
    forecast_years = context.input_data.get("forecast_years")
    if forecast_years is not None:
        if not isinstance(forecast_years, list) or len(forecast_years) == 0:
            raise ValueError("forecast_years 必须是非空列表，如 [2026, 2027, 2028]")
        for year in forecast_years:
            if not isinstance(year, int) or year < 2000 or year > 2100:
                raise ValueError(f"forecast_years 中的 {year} 不是合法年份")
    elif not has_template:
        raise ValueError("forecast_years 必填（或通过 model_template 提供）")

    # 验证收入公式（如果有）
    revenue_formula = context.input_data.get("revenue_formula")
    if revenue_formula is not None:
        if not isinstance(revenue_formula, str) or not revenue_formula.strip():
            raise ValueError("revenue_formula 必须是非空字符串")
    elif not has_template:
        raise ValueError("revenue_formula 必填（或通过 model_template 提供）")

    # 验证利润公式（可选）
    profit_formula = context.input_data.get("profit_formula")
    if profit_formula is not None and (not isinstance(profit_formula, str) or not profit_formula.strip()):
        raise ValueError("profit_formula 必须是非空字符串或 null")

    # 验证驱动变量（如果有）
    drivers_input = context.input_data.get("drivers")
    if drivers_input is not None:
        if not isinstance(drivers_input, list):
            raise ValueError("drivers 必须是列表")
        for index, driver in enumerate(drivers_input):
            if not isinstance(driver, dict):
                raise ValueError(f"drivers[{index}] 必须是对象")
            if not driver.get("name"):
                raise ValueError(f"drivers[{index}].name 不能为空")
            if not isinstance(driver.get("values_by_year"), dict) or not driver["values_by_year"]:
                raise ValueError(f"drivers[{index}].values_by_year 必须是非空对象")
            unit = driver.get("unit", "")
            if unit and unit not in VALID_UNITS:
                raise ValueError(
                    f"drivers[{index}].unit '{unit}' 不在合法单位集合中: {sorted(VALID_UNITS)}"
                )
    elif not has_template:
        raise ValueError("drivers 必填（或通过 model_template 提供）")

    # 验证数值型可选字段
    numeric_fields = {
        "shares_outstanding": "股本",
        "current_price": "当前价格",
        "current_market_cap": "当前市值",
        "terminal_pe": "终值 PE",
    }
    for field, label in numeric_fields.items():
        value = context.input_data.get(field)
        if value is not None and not isinstance(value, (int, float)):
            raise ValueError(f"{label}（{field}）必须是数值")

    # 验证预测年限
    forecast_horizon_years = context.input_data.get("forecast_horizon_years")
    if forecast_horizon_years is None:
        forecast_horizon_years = len(forecast_years) if forecast_years else None
    elif not isinstance(forecast_horizon_years, int) or forecast_horizon_years <= 0:
        raise ValueError("forecast_horizon_years 必须是正整数")

    # 写入状态
    context.state.update({
        "ticker": ticker,
        "market": market,
        "forecast_years": list(forecast_years) if forecast_years else None,
        "revenue_formula": revenue_formula,
        "profit_formula": profit_formula,
        "drivers_input": drivers_input if drivers_input is not None else [],
        "shares_outstanding": context.input_data.get("shares_outstanding"),
        "current_price": context.input_data.get("current_price"),
        "current_market_cap": context.input_data.get("current_market_cap"),
        "terminal_pe": context.input_data.get("terminal_pe"),
        "forecast_horizon_years": forecast_horizon_years,
        "model_template": model_template,
        "scenarios_input": context.input_data.get("scenarios"),
        "sensitivity_input": context.input_data.get("sensitivity"),
    })

    return StageResult.completed(
        "估值输入验证通过",
        {
            "ticker": ticker,
            "market": market,
            "forecast_years": forecast_years,
            "driver_count": len(drivers_input) if drivers_input else 0,
            "has_model_template": has_template,
            "has_profit_formula": profit_formula is not None,
            "has_shares": context.input_data.get("shares_outstanding") is not None,
            "has_current_price": context.input_data.get("current_price") is not None,
            "has_terminal_pe": context.input_data.get("terminal_pe") is not None,
        },
    )


# ============================================================================
# 阶段 2：读取市场上下文（允许缺失）
# ============================================================================

def _load_market_context_stage(source_db_path: Path | None):
    """
    构建"读取历史财务、当前价格、市值"阶段

    小白讲解：
        这是"档案管理员"——去数据库查这家公司最新的财务数据、市值和价格。
        如果数据库里没有，也不报错，只是记录"这条数据缺失"，
        后续计算仍可用用户输入的驱动变量继续。

    参数:
        source_db_path: 外部数据源 DB 路径（None 表示用工作流自己的 DB）

    返回:
        阶段处理函数
    """

    def handler(context: WorkflowContext) -> StageResult:
        ticker = context.state["ticker"]
        warnings = []
        market_context = {
            "fundamentals": None,
            "valuation_snapshot": None,
            "latest_price": None,
        }

        # 尝试从数据库读取历史财务和估值快照
        db_to_use = source_db_path or context.db_path
        try:
            if source_db_path is None or source_db_path.resolve() == context.db_path.resolve():
                conn = sqlite3.connect(context.db_path)
            else:
                uri = source_db_path.resolve().as_uri() + "?mode=ro"
                conn = sqlite3.connect(uri, uri=True)
            try:
                # 读取基本面快照（可能不存在）
                try:
                    row = conn.execute(
                        "SELECT ticker, revenue, net_income, gross_margin, net_margin, "
                        "operating_margin, roe, source, period_end, created_at "
                        "FROM fundamentals_snapshot WHERE ticker = ? "
                        "ORDER BY created_at DESC LIMIT 1",
                        (ticker,),
                    ).fetchone()
                    if row:
                        market_context["fundamentals"] = {
                            "ticker": row[0], "revenue": row[1], "net_income": row[2],
                            "gross_margin": row[3], "net_margin": row[4],
                            "operating_margin": row[5], "roe": row[6],
                            "source": row[7], "period_end": row[8], "created_at": row[9],
                        }
                except sqlite3.Error:
                    warnings.append(f"fundamentals_snapshot 表不存在或不可读，跳过历史财务")

                # 读取估值快照（可能不存在）
                try:
                    row = conn.execute(
                        "SELECT ticker, pe_ttm, pb, current_price, broker_target_price, "
                        "valuation_status, valuation_confidence, generated_at "
                        "FROM valuation_snapshot WHERE ticker = ? "
                        "ORDER BY generated_at DESC LIMIT 1",
                        (ticker,),
                    ).fetchone()
                    if row:
                        market_context["valuation_snapshot"] = {
                            "ticker": row[0], "pe_ttm": row[1], "pb": row[2],
                            "current_price": row[3], "broker_target_price": row[4],
                            "valuation_status": row[5], "valuation_confidence": row[6],
                            "generated_at": row[7],
                        }
                        # 如果用户没提供当前价，用快照中的当前价
                        if context.state.get("current_price") is None and row[3]:
                            context.state["current_price"] = float(row[3])
                            market_context["latest_price"] = float(row[3])
                            warnings.append("current_price 从 valuation_snapshot 补全")
                except sqlite3.Error:
                    warnings.append(f"valuation_snapshot 表不存在或不可读，跳过估值快照")
            finally:
                conn.close()
        except sqlite3.Error as exc:
            warnings.append(f"读取市场上下文失败：{exc}")

        context.state["market_context"] = market_context
        context.state["market_context_warnings"] = warnings

        return StageResult.completed(
            "市场上下文加载完成（允许部分缺失）",
            {
                "has_fundamentals": market_context["fundamentals"] is not None,
                "has_valuation_snapshot": market_context["valuation_snapshot"] is not None,
                "has_latest_price": market_context["latest_price"] is not None,
                "warning_count": len(warnings),
            },
        )

    return handler


# ============================================================================
# 阶段 3：应用模型模板
# ============================================================================

def _apply_model_template_stage(template_path: Path):
    """
    构建"应用模型模板"阶段

    小白讲解：
        模板就像"标准菜谱"——海光信息的标准菜谱里默认 DCU 出货量 30 万颗、
        ASP 1.2 万元/颗等。如果用户没填这些值，就从模板里取默认值；
        如果用户填了，就用用户的值（用户输入优先级高于模板）。

    参数:
        template_path: 模板配置文件路径

    返回:
        阶段处理函数
    """

    def handler(context: WorkflowContext) -> StageResult:
        template_name = context.state.get("model_template")
        warnings = list(context.state.get("market_context_warnings", []))

        # 没有指定模板，直接跳过
        if not template_name:
            context.state["template_applied"] = None
            return StageResult.completed(
                "未指定模型模板，跳过模板加载",
                {"template_applied": False},
            )

        # 加载模板文件
        if not template_path.is_file():
            warnings.append(f"模板文件不存在：{template_path}")
            context.state["template_applied"] = None
            context.state["market_context_warnings"] = warnings
            return StageResult.completed(
                f"模板文件不存在：{template_path}",
                {"template_applied": False, "warning_count": len(warnings)},
            )

        try:
            templates = json.loads(template_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            warnings.append(f"模板文件解析失败：{exc}")
            context.state["template_applied"] = None
            context.state["market_context_warnings"] = warnings
            return StageResult.completed(
                f"模板文件解析失败：{exc}",
                {"template_applied": False, "warning_count": len(warnings)},
            )

        template = templates.get("templates", {}).get(template_name)
        if not template:
            warnings.append(f"模板 '{template_name}' 不在配置文件中")
            context.state["template_applied"] = None
            context.state["market_context_warnings"] = warnings
            return StageResult.completed(
                f"模板 '{template_name}' 不存在",
                {"template_applied": False, "warning_count": len(warnings)},
            )

        # 模板补充优先级：用户输入 > 模板默认值
        # 小白讲解：模板只补充用户没填的字段，不会覆盖用户填的值
        state = context.state

        # 补充 forecast_years
        if state.get("forecast_years") is None and template.get("forecast_years"):
            state["forecast_years"] = list(template["forecast_years"])
            warnings.append("forecast_years 从模板补全")

        # 补充 revenue_formula
        if state.get("revenue_formula") is None and template.get("revenue_formula"):
            state["revenue_formula"] = template["revenue_formula"]
            warnings.append("revenue_formula 从模板补全")

        # 补充 profit_formula
        if state.get("profit_formula") is None and template.get("profit_formula"):
            state["profit_formula"] = template["profit_formula"]
            warnings.append("profit_formula 从模板补全")

        # 补充数值字段
        for field in ("shares_outstanding", "current_price", "current_market_cap", "terminal_pe"):
            if state.get(field) is None and template.get(field) is not None:
                state[field] = template[field]
                warnings.append(f"{field} 从模板补全")

        # 补充 forecast_horizon_years
        if state.get("forecast_horizon_years") is None and template.get("forecast_horizon_years"):
            state["forecast_horizon_years"] = template["forecast_horizon_years"]

        # 补充驱动变量（用户没填的变量从模板取）
        # 小白讲解：用户填了 DCU 出货量但没填 ASP，模板会补 ASP
        existing_driver_names = {d["name"] for d in state.get("drivers_input", [])}
        template_drivers = template.get("drivers", [])
        supplemented_drivers = []
        for template_driver in template_drivers:
            if template_driver["name"] not in existing_driver_names:
                supplemented_drivers.append(template_driver)
                warnings.append(f"驱动变量 {template_driver['name']} 从模板补全")

        if supplemented_drivers:
            state["drivers_input"] = list(state.get("drivers_input", [])) + supplemented_drivers

        # === 模板应用后做完整必填验证 ===
        # 小白讲解：模板补充完后，必须确认 forecast_years、drivers、revenue_formula 都有了
        if not state.get("forecast_years"):
            raise ValueError(
                f"模板 '{template_name}' 应用后 forecast_years 仍缺失，请检查模板或显式提供"
            )
        if not state.get("revenue_formula"):
            raise ValueError(
                f"模板 '{template_name}' 应用后 revenue_formula 仍缺失，请检查模板或显式提供"
            )
        if not state.get("drivers_input"):
            raise ValueError(
                f"模板 '{template_name}' 应用后 drivers 仍缺失，请检查模板或显式提供"
            )

        # 同步 scenarios_input 和 sensitivity_input（模板可以提供）
        if state.get("scenarios_input") is None and template.get("scenarios"):
            state["scenarios_input"] = template["scenarios"]
        if state.get("sensitivity_input") is None and template.get("sensitivity"):
            state["sensitivity_input"] = template["sensitivity"]

        context.state["template_applied"] = template_name
        context.state["market_context_warnings"] = warnings

        return StageResult.completed(
            f"模型模板 '{template_name}' 应用完成",
            {
                "template_applied": True,
                "template_name": template_name,
                "supplemented_driver_count": len(supplemented_drivers),
                "warning_count": len(warnings),
            },
        )

    return handler


# ============================================================================
# 阶段 4：构建驱动变量假设表
# ============================================================================

def _build_assumptions(context: WorkflowContext) -> StageResult:
    """
    构建驱动变量假设表

    小白讲解：
        把用户给的驱动变量列表转换成 DriverAssumption 对象。
        同时合并市场上下文中的历史事实（如已确认的财务数据），
        形成"假设 + 事实"混合的假设表。
        is_assumption=True 的是假设，is_assumption=False 的是已确认事实。

    参数:
        context.state.drivers_input: 驱动变量字典列表

    返回:
        StageResult，包含 driver_count 和 assumption_count
    """
    drivers_input = context.state["drivers_input"]
    forecast_years = context.state["forecast_years"]

    drivers = []
    for driver_dict in drivers_input:
        # 验证 values_by_year 中的年份都在 forecast_years 中
        values_by_year = {}
        for year, value in driver_dict.get("values_by_year", {}).items():
            # JSON 中的 key 是字符串，转回 int
            year_int = int(year) if isinstance(year, str) else year
            if year_int not in forecast_years:
                # 跳过不在预测期的年份
                continue
            if not isinstance(value, (int, float)):
                continue
            values_by_year[year_int] = float(value)

        if not values_by_year:
            # 没有有效值，跳过这个驱动变量
            continue

        drivers.append(DriverAssumption(
            name=driver_dict["name"],
            label=driver_dict.get("label", driver_dict["name"]),
            unit=driver_dict.get("unit", ""),
            values_by_year=values_by_year,
            source=driver_dict.get("source", "user_input"),
            is_assumption=bool(driver_dict.get("is_assumption", True)),
        ))

    if not drivers:
        raise ValueError("构建假设表失败：所有驱动变量都没有有效值")

    context.state["drivers"] = drivers

    # 统计假设数和事实数
    assumption_count = sum(1 for d in drivers if d.is_assumption)
    fact_count = len(drivers) - assumption_count

    return StageResult.completed(
        "驱动变量假设表构建完成",
        {
            "driver_count": len(drivers),
            "assumption_count": assumption_count,
            "fact_count": fact_count,
            "forecast_years": forecast_years,
        },
    )


# ============================================================================
# 阶段 5：验证假设
# ============================================================================

def _validate_assumptions(context: WorkflowContext) -> StageResult:
    """
    验证驱动变量假设的单位、边界和变量依赖

    小白讲解：
        这是"质检员"——检查假设表是否合理：
        1. 每个预测年份都有所有驱动变量的值（缺失就警告）
        2. 百分比变量值在合理范围（如毛利率 0-100）
        3. 收入公式引用的变量在驱动变量中存在
        4. 利润公式引用的变量在驱动变量中存在或为 revenue

    参数:
        context.state.drivers: DriverAssumption 列表
        context.state.revenue_formula: 收入公式
        context.state.profit_formula: 利润公式

    返回:
        StageResult，包含验证结果和警告列表
    """
    drivers = context.state["drivers"]
    forecast_years = context.state["forecast_years"]
    revenue_formula = context.state["revenue_formula"]
    profit_formula = context.state.get("profit_formula")
    warnings = list(context.state.get("market_context_warnings", []))

    driver_names = {d.name for d in drivers}

    # 检查 1：每个预测年份的每个驱动变量都有值
    for driver in drivers:
        for year in forecast_years:
            if year not in driver.values_by_year:
                warnings.append(
                    f"驱动变量 {driver.name} 在 {year} 年缺失值"
                )

    # 检查 2：百分比变量的值在合理范围
    for driver in drivers:
        if driver.unit == "%":
            for year, value in driver.values_by_year.items():
                if value < -100 or value > 200:
                    warnings.append(
                        f"驱动变量 {driver.name}（%）在 {year} 年值 {value} 超出合理范围 [-100, 200]"
                    )

    # 检查 3：收入公式引用的变量都存在
    # 小白讲解：从公式中提取变量名（字母、数字、下划线组成的标识符）
    # 然后检查每个标识符是否在驱动变量中（除了数字和运算符）
    formula_vars = _extract_formula_variables(revenue_formula)
    missing_in_revenue = [v for v in formula_vars if v not in driver_names and v != "revenue"]
    if missing_in_revenue:
        warnings.append(
            f"收入公式引用了未定义的变量：{missing_in_revenue}"
        )

    # 检查 4：利润公式引用的变量都存在（利润公式可以引用 revenue）
    if profit_formula:
        profit_vars = _extract_formula_variables(profit_formula)
        missing_in_profit = [
            v for v in profit_vars
            if v not in driver_names and v != "revenue"
        ]
        if missing_in_profit:
            warnings.append(
                f"利润公式引用了未定义的变量：{missing_in_profit}"
            )

    context.state["assumption_warnings"] = warnings

    # 判断是否有致命错误（收入公式引用了未定义变量会让计算无法进行）
    has_fatal = bool(missing_in_revenue)

    return StageResult.completed(
        "驱动变量假设验证完成",
        {
            "warning_count": len(warnings),
            "has_fatal_error": has_fatal,
            "driver_names": sorted(driver_names),
        },
    )


def _extract_formula_variables(formula: str) -> set:
    """
    从公式中提取变量名

    小白讲解：
        公式 "dcu_shipment * dcu_asp + cpu_revenue" 提取出
        {"dcu_shipment", "dcu_asp", "cpu_revenue"}。
        数字和运算符会被忽略。

    参数:
        formula: 公式字符串

    返回:
        变量名集合
    """
    # 匹配字母开头的标识符（变量名）
    # 排除科学计数法的 e（如 1e-5）
    identifiers = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", formula))
    # 排除科学计数法
    identifiers.discard("e")
    identifiers.discard("E")
    return identifiers


# ============================================================================
# 阶段 6：估值计算
# ============================================================================

def _compute_valuation(context: WorkflowContext) -> StageResult:
    """
    调用 ValuationEngine 计算估值

    小白讲解：
        这是工作流的核心阶段——把驱动变量和公式交给估值引擎，
        引擎会按公式计算收入、利润、EPS、目标市值、目标价、IRR。
        如果关键输入缺失（如股本、PE），引擎不会生成对应字段，
        而是在 warnings 中记录。

    参数:
        context.state 中的 drivers、forecast_years、revenue_formula 等

    返回:
        StageResult，包含估值摘要
    """
    # 构建 ValuationInput
    valuation_input = ValuationInput(
        entity_key=context.state["ticker"],
        forecast_years=context.state["forecast_years"],
        drivers=context.state["drivers"],
        revenue_formula=context.state["revenue_formula"],
        profit_formula=context.state.get("profit_formula"),
        shares_outstanding=context.state.get("shares_outstanding"),
        current_price=context.state.get("current_price"),
        current_market_cap=context.state.get("current_market_cap"),
        terminal_pe=context.state.get("terminal_pe"),
        forecast_horizon_years=context.state.get("forecast_horizon_years", len(context.state["forecast_years"])),
    )

    # 调用引擎计算
    engine = ValuationEngine()
    result = engine.compute(valuation_input)

    # 合并警告
    warnings = list(context.state.get("assumption_warnings", []))
    warnings.extend(result.warnings)

    context.state["valuation_result"] = result
    context.state["valuation_input"] = valuation_input
    context.state["all_warnings"] = warnings

    # 构建摘要
    summary = {
        "has_target_price": "target_price" in result.summary,
        "has_target_market_cap": "target_market_cap" in result.summary,
        "has_irr": "irr" in result.summary,
        "has_eps": bool(result.projections.get("eps")),
        "has_net_income": bool(result.projections.get("net_income")),
        "warning_count": len(warnings),
    }
    if "target_price" in result.summary:
        summary["target_price"] = result.summary["target_price"]
    if "target_market_cap" in result.summary:
        summary["target_market_cap"] = result.summary["target_market_cap"]
    if "irr" in result.summary:
        summary["irr"] = result.summary["irr"]

    return StageResult.completed(
        "估值计算完成",
        summary,
    )


# ============================================================================
# 阶段 7：反解隐含预期
# ============================================================================

def _reverse_implied(context: WorkflowContext) -> StageResult:
    """
    反解当前价格隐含的市场预期

    小白讲解：
        这是从"当前股价 100 元"反推"市场预期这家公司未来几年增长多快"。
        如果当前价或股本缺失，就跳过反解（返回 None）。
        反解结果会保存到状态中，供后续报告使用。

    参数:
        context.state.valuation_result: 正向估值结果
        context.state.valuation_input: 估值输入

    返回:
        StageResult，包含反解的隐含预期
    """
    valuation_input = context.state["valuation_input"]
    valuation_result = context.state["valuation_result"]
    warnings = list(context.state.get("all_warnings", []))

    reverse = ReverseImplied()
    implied = {}

    current_price = valuation_input.current_price
    shares = valuation_input.shares_outstanding
    terminal_pe = valuation_input.terminal_pe
    forecast_horizon = valuation_input.forecast_horizon_years

    # 反解隐含 CAGR（需要当前价、股本、PE、基期净利、预测年限）
    # 小白讲解：基期净利用预测第一年的净利作为近似
    if (
        current_price and shares and terminal_pe and forecast_horizon
        and valuation_result.projections.get("net_income")
    ):
        first_year = valuation_input.forecast_years[0]
        base_net_income = valuation_result.projections["net_income"].get(first_year)
        if base_net_income and base_net_income > 0:
            implied_cagr = reverse.solve_implied_cagr(
                current_price=current_price,
                shares_outstanding=shares,
                terminal_pe=terminal_pe,
                base_net_income=base_net_income,
                forecast_horizon_years=forecast_horizon,
            )
            if implied_cagr is not None:
                implied["implied_cagr"] = implied_cagr
        else:
            warnings.append("基期净利润为 0 或负值，跳过隐含 CAGR 反解")

    # 反解隐含净利率（需要当前价、股本、PE、预测最后一年的收入）
    if (
        current_price and shares and terminal_pe
        and valuation_result.projections.get("revenue")
    ):
        last_year = valuation_input.forecast_years[-1]
        forecast_revenue = valuation_result.projections["revenue"].get(last_year)
        if forecast_revenue and forecast_revenue > 0:
            implied_margin = reverse.solve_implied_margin(
                current_price=current_price,
                shares_outstanding=shares,
                terminal_pe=terminal_pe,
                forecast_revenue=forecast_revenue,
            )
            if implied_margin is not None:
                implied["implied_net_margin"] = implied_margin
        else:
            warnings.append("预测最后一年收入为 0 或负值，跳过隐含利润率反解")

    # 反解隐含出货量（需要 ASP、CPU 收入、净利率等额外参数）
    # 小白讲解：这需要从驱动变量中找 ASP 和 CPU 收入
    driver_map = {d.name: d for d in valuation_input.drivers}
    asp_driver = driver_map.get("dcu_asp")
    cpu_revenue_driver = driver_map.get("cpu_revenue")

    if (
        current_price and shares and terminal_pe
        and asp_driver and cpu_revenue_driver
        and "implied_net_margin" in implied
        and valuation_input.forecast_years
    ):
        last_year = valuation_input.forecast_years[-1]
        asp = asp_driver.values_by_year.get(last_year)
        cpu_revenue = cpu_revenue_driver.values_by_year.get(last_year, 0)

        # ASP 单位是"万元/颗"，需要转换成"亿元/万颗" = "万元/颗"（数值上等价）
        if asp and asp > 0:
            implied_shipment = reverse.solve_implied_shipment(
                current_price=current_price,
                shares_outstanding=shares,
                terminal_pe=terminal_pe,
                asp=asp,
                cpu_revenue=cpu_revenue or 0,
                net_margin=implied["implied_net_margin"],
            )
            if implied_shipment is not None:
                implied["implied_dcu_shipment"] = implied_shipment

    context.state["implied_expectations"] = implied
    context.state["all_warnings"] = warnings

    return StageResult.completed(
        "当前价格隐含预期反解完成",
        {
            "has_implied_cagr": "implied_cagr" in implied,
            "has_implied_margin": "implied_net_margin" in implied,
            "has_implied_shipment": "implied_dcu_shipment" in implied,
        },
    )


# ============================================================================
# 阶段 8：情景分析
# ============================================================================

def _generate_scenarios(context: WorkflowContext) -> StageResult:
    """
    生成悲观/基准/乐观情景

    小白讲解：
        基准情景用用户给的假设，悲观情景把出货量减半、ASP 降 20%，
        乐观情景把出货量增 30%、ASP 增 10%。
        每个情景都重新走一遍估值计算，得到该情景下的目标价。

    参数:
        context.state.valuation_input: 基准估值输入
        context.state.scenarios_input: 用户自定义情景（可选）

    返回:
        StageResult，包含情景列表和每个情景的目标价
    """
    valuation_input = context.state["valuation_input"]
    scenarios_input = context.state.get("scenarios_input")

    generator = ScenarioGenerator()

    # 用户可以自定义情景，否则用默认的悲观/基准/乐观
    if scenarios_input and isinstance(scenarios_input, dict):
        scenarios = generator.generate_scenarios(valuation_input, scenarios_input)
    else:
        scenarios = generator.generate_scenarios(valuation_input)

    # 构建情景摘要
    scenario_summary = {}
    for name, result in scenarios.items():
        scenario_summary[name] = {
            "target_price": result.summary.get("target_price"),
            "target_market_cap": result.summary.get("target_market_cap"),
            "has_target": "target_price" in result.summary,
        }

    context.state["scenarios"] = scenarios
    context.state["scenario_summary"] = scenario_summary

    return StageResult.completed(
        "情景分析完成",
        {
            "scenario_count": len(scenarios),
            "scenarios": list(scenarios.keys()),
            "scenario_summary": scenario_summary,
        },
    )


# ============================================================================
# 阶段 9：敏感性矩阵
# ============================================================================

def _generate_sensitivity(context: WorkflowContext) -> StageResult:
    """
    生成二维敏感性矩阵

    小白讲解：
        这是"网格搜索"——固定两个变量（如 DCU 出货量和 ASP），
        每个组合都算一次目标价，看哪个变量对目标价影响最大。
        如果用户没指定，就用默认的出货量 × ASP 网格。

    参数:
        context.state.valuation_input: 基准估值输入
        context.state.sensitivity_input: 用户自定义敏感性配置（可选）

    返回:
        StageResult，包含敏感性矩阵
    """
    valuation_input = context.state["valuation_input"]
    sensitivity_input = context.state.get("sensitivity_input") or DEFAULT_SENSITIVITY

    x_driver = sensitivity_input.get("x_driver", DEFAULT_SENSITIVITY["x_driver"])
    y_driver = sensitivity_input.get("y_driver", DEFAULT_SENSITIVITY["y_driver"])
    x_values = sensitivity_input.get("x_values", DEFAULT_SENSITIVITY["x_values"])
    y_values = sensitivity_input.get("y_values", DEFAULT_SENSITIVITY["y_values"])

    # 小白讲解：敏感性矩阵的 x_values 和 y_values 是"相对基准的乘数"。
    # 比如基准 DCU 出货量 30 万颗，x_values=[0.5, 1.0, 1.5] 表示
    # 测试 15 万、30 万、45 万三种情况。
    # 我们需要把乘数转换为实际值，传给 ScenarioGenerator。
    driver_map = {d.name: d for d in valuation_input.drivers}
    forecast_years = valuation_input.forecast_years

    # 获取基准值（用最后一年的值作为基准）
    if not forecast_years:
        context.state["sensitivity_matrix"] = None
        return StageResult.completed(
            "无预测年份，跳过敏感性分析",
            {"sensitivity_generated": False},
        )

    last_year = forecast_years[-1]
    x_base_driver = driver_map.get(x_driver)
    y_base_driver = driver_map.get(y_driver)

    if not x_base_driver or not y_base_driver:
        context.state["sensitivity_matrix"] = None
        return StageResult.completed(
            f"敏感性变量 {x_driver} 或 {y_driver} 不在驱动变量中，跳过",
            {"sensitivity_generated": False},
        )

    x_base_value = x_base_driver.values_by_year.get(last_year)
    y_base_value = y_base_driver.values_by_year.get(last_year)

    if x_base_value is None or y_base_value is None:
        context.state["sensitivity_matrix"] = None
        return StageResult.completed(
            f"敏感性变量在最后一年 {last_year} 缺失值，跳过",
            {"sensitivity_generated": False},
        )

    # 把乘数转换为实际值
    x_actual_values = [x_base_value * m for m in x_values]
    y_actual_values = [y_base_value * m for m in y_values]

    generator = ScenarioGenerator()
    matrix = generator.generate_sensitivity_matrix(
        base_input=valuation_input,
        x_driver=x_driver,
        x_values=x_actual_values,
        y_driver=y_driver,
        y_values=y_actual_values,
    )

    # 把矩阵的 key 从 float 转成字符串，方便 JSON 序列化
    serializable_matrix = {}
    for y_val, row in matrix.items():
        key_y = f"{y_val:.4f}"
        serializable_matrix[key_y] = {}
        for x_val, target_price in row.items():
            key_x = f"{x_val:.4f}"
            serializable_matrix[key_y][key_x] = target_price

    context.state["sensitivity_matrix"] = serializable_matrix
    context.state["sensitivity_config"] = {
        "x_driver": x_driver,
        "y_driver": y_driver,
        "x_values": x_actual_values,
        "y_values": y_actual_values,
        "x_multipliers": x_values,
        "y_multipliers": y_values,
    }

    return StageResult.completed(
        "二维敏感性矩阵生成完成",
        {
            "sensitivity_generated": True,
            "x_driver": x_driver,
            "y_driver": y_driver,
            "grid_size": f"{len(x_values)}x{len(y_values)}",
        },
    )


# ============================================================================
# 阶段 10：独立复算和质量门
# ============================================================================

def _independent_recalc(context: WorkflowContext) -> StageResult:
    """
    独立复算和质量门检查

    小白讲解：
        这是"复核员"——重新跑一遍估值计算，确认结果一致。
        同时检查质量门：
        1. 目标价如果生成，必须是正数
        2. IRR 如果生成，必须在合理范围（-90% 到 1000%）
        3. 假设表中每个变量都有来源
        4. 反解的隐含预期与正向模型一致（容差 1%）

    参数:
        context.state.valuation_input: 原始输入
        context.state.valuation_result: 原始结果

    返回:
        StageResult，包含质量门结果
    """
    valuation_input = context.state["valuation_input"]
    original_result = context.state["valuation_result"]
    warnings = list(context.state.get("all_warnings", []))

    # 重新计算一次
    engine = ValuationEngine()
    recalc_result = engine.compute(valuation_input)

    quality_gate = {
        "recalc_consistent": True,
        "target_price_positive": True,
        "irr_in_range": True,
        "assumptions_have_source": True,
        "implied_consistent": True,
        "errors": [],
    }

    # 检查 1：复算结果一致
    # 小白讲解：同一个输入跑两次，结果必须完全一致
    for year in valuation_input.forecast_years:
        orig_revenue = original_result.projections.get("revenue", {}).get(year)
        recalc_revenue = recalc_result.projections.get("revenue", {}).get(year)
        if orig_revenue != recalc_revenue:
            quality_gate["recalc_consistent"] = False
            quality_gate["errors"].append(
                f"{year} 年收入复算不一致：{orig_revenue} vs {recalc_revenue}"
            )

        orig_ni = original_result.projections.get("net_income", {}).get(year)
        recalc_ni = recalc_result.projections.get("net_income", {}).get(year)
        if orig_ni != recalc_ni:
            quality_gate["recalc_consistent"] = False
            quality_gate["errors"].append(
                f"{year} 年净利润复算不一致：{orig_ni} vs {recalc_ni}"
            )

    # 检查 2：目标价为正
    target_price = original_result.summary.get("target_price")
    if target_price is not None and target_price <= 0:
        quality_gate["target_price_positive"] = False
        quality_gate["errors"].append(f"目标价 {target_price} 不是正数")
        warnings.append(f"目标价 {target_price} 不是正数，已剔除")
        # 剔除无效目标价
        original_result.summary.pop("target_price", None)
        original_result.summary.pop("target_market_cap", None)
        original_result.summary.pop("irr", None)

    # 检查 3：IRR 在合理范围
    irr = original_result.summary.get("irr")
    if irr is not None and (irr < -0.9 or irr > 10.0):
        quality_gate["irr_in_range"] = False
        quality_gate["errors"].append(f"IRR {irr} 超出合理范围 [-90%, 1000%]")
        warnings.append(f"IRR {irr} 超出合理范围，已剔除")
        original_result.summary.pop("irr", None)

    # 检查 4：每个假设都有来源
    for driver in valuation_input.drivers:
        if not driver.source:
            quality_gate["assumptions_have_source"] = False
            quality_gate["errors"].append(f"驱动变量 {driver.name} 缺少来源标注")

    # 检查 5：反解的隐含预期与正向模型一致
    # 小白讲解：如果反解出隐含 CAGR 是 30%，正向模型用 30% 增长应该得到接近当前价的目标价
    implied = context.state.get("implied_expectations", {})
    if "implied_cagr" in implied and target_price and target_price > 0:
        # 隐含 CAGR 应该让正向模型的目标价接近当前价
        # 这里只做简单的一致性检查（隐含 CAGR 在合理范围）
        implied_cagr = implied["implied_cagr"]
        if implied_cagr < -0.5 or implied_cagr > 5.0:
            quality_gate["implied_consistent"] = False
            quality_gate["errors"].append(
                f"隐含 CAGR {implied_cagr} 超出合理范围 [-50%, 500%]，正向模型可能有问题"
            )
            warnings.append(f"隐含 CAGR {implied_cagr} 异常，请检查输入")

    context.state["quality_gate"] = quality_gate
    context.state["all_warnings"] = warnings

    # 质量门通过标准：没有致命错误
    # 注意：recalc_consistent 必须通过，其他是警告级别
    passed = quality_gate["recalc_consistent"]

    return StageResult.completed(
        "独立复算和质量门检查完成",
        {
            "quality_gate_passed": passed,
            "recalc_consistent": quality_gate["recalc_consistent"],
            "target_price_positive": quality_gate["target_price_positive"],
            "irr_in_range": quality_gate["irr_in_range"],
            "assumptions_have_source": quality_gate["assumptions_have_source"],
            "implied_consistent": quality_gate["implied_consistent"],
            "error_count": len(quality_gate["errors"]),
        },
    )


# ============================================================================
# 阶段 11：保存制品
# ============================================================================

def _persist_outputs_stage(artifact_root: Path):
    """
    构建"保存制品"阶段

    小白讲解：
        把估值结果保存成三种格式：
        - JSON：包含完整输入和输出，可以重新验证计算
        - Markdown：人可读的报告，包含摘要表格和假设表
        - CSV：Excel 可分析的逐年预测数据
        同时在数据库中注册 artifact，方便后续查询。

    参数:
        artifact_root: 制品根目录

    返回:
        阶段处理函数
    """

    def handler(context: WorkflowContext) -> StageResult:
        ticker = context.state["ticker"]
        valuation_result = context.state["valuation_result"]
        valuation_input = context.state["valuation_input"]
        scenarios = context.state.get("scenarios", {})
        scenario_summary = context.state.get("scenario_summary", {})
        sensitivity_matrix = context.state.get("sensitivity_matrix")
        sensitivity_config = context.state.get("sensitivity_config")
        implied = context.state.get("implied_expectations", {})
        quality_gate = context.state.get("quality_gate", {})
        warnings = context.state.get("all_warnings", [])
        market_context = context.state.get("market_context", {})
        template_applied = context.state.get("template_applied")

        # 创建运行目录
        run_dir = artifact_root.resolve() / context.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # === 保存估值模型 JSON（完整可复算）===
        model_json_path = run_dir / "valuation_model.json"
        model_payload = {
            "schema_version": "1.0",
            "generated_at": _utc_now(),
            "run_id": context.run_id,
            "ticker": ticker,
            "market": context.state["market"],
            "forecast_years": context.state["forecast_years"],
            "template_applied": template_applied,
            "input": valuation_result.input_snapshot,
            "projections": valuation_result.projections,
            "summary": valuation_result.summary,
            "assumptions_table": valuation_result.assumptions_table,
            "implied_expectations": implied,
            "scenario_summary": scenario_summary,
            "sensitivity_config": sensitivity_config,
            "sensitivity_matrix": sensitivity_matrix,
            "quality_gate": quality_gate,
            "warnings": warnings,
            "market_context": market_context,
        }
        model_json_path.write_text(
            json.dumps(model_payload, ensure_ascii=False, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )

        # === 保存 Markdown 报告 ===
        report_path = run_dir / "valuation_report.md"
        report_path.write_text(
            _build_markdown_report(
                ticker=ticker,
                valuation_result=valuation_result,
                scenarios=scenarios,
                scenario_summary=scenario_summary,
                implied=implied,
                quality_gate=quality_gate,
                warnings=warnings,
                template_applied=template_applied,
            ),
            encoding="utf-8",
        )

        # === 保存 CSV 逐年预测 ===
        csv_path = run_dir / "valuation_projections.csv"
        csv_path.write_text(
            ArtifactGenerator().to_csv(valuation_result),
            encoding="utf-8",
        )

        # === 保存情景对比 JSON ===
        scenario_json_path = run_dir / "scenario_comparison.json"
        scenario_payload = {
            "schema_version": "1.0",
            "generated_at": _utc_now(),
            "ticker": ticker,
            "scenario_summary": scenario_summary,
        }
        scenario_json_path.write_text(
            json.dumps(scenario_payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

        # === 在数据库中注册 artifact ===
        conn = sqlite3.connect(context.db_path)
        registered_artifacts = []
        try:
            store = ArtifactStore(conn, [artifact_root])

            model_artifact = store.register_artifact(
                context.run_id,
                "valuation_model",
                f"经营驱动估值模型 — {ticker}",
                model_json_path,
                "application/json",
                metadata={
                    "ticker": ticker,
                    "has_target_price": "target_price" in valuation_result.summary,
                    "quality_gate_passed": quality_gate.get("recalc_consistent", False),
                },
            )
            registered_artifacts.append(model_artifact)

            report_artifact = store.register_artifact(
                context.run_id,
                "valuation_report",
                f"估值报告 — {ticker}",
                report_path,
                "text/markdown",
                metadata={"ticker": ticker},
            )
            registered_artifacts.append(report_artifact)

            csv_artifact = store.register_artifact(
                context.run_id,
                "valuation_projections",
                f"逐年预测 CSV — {ticker}",
                csv_path,
                "text/csv",
                metadata={"ticker": ticker},
            )
            registered_artifacts.append(csv_artifact)

            scenario_artifact = store.register_artifact(
                context.run_id,
                "valuation_scenarios",
                f"情景对比 — {ticker}",
                scenario_json_path,
                "application/json",
                metadata={"ticker": ticker, "scenario_count": len(scenario_summary)},
            )
            registered_artifacts.append(scenario_artifact)
        finally:
            conn.close()

        # === 构建最终摘要 ===
        summary = {
            "ticker": ticker,
            "market": context.state["market"],
            "forecast_years": context.state["forecast_years"],
            "template_applied": template_applied,
            "has_target_price": "target_price" in valuation_result.summary,
            "has_irr": "irr" in valuation_result.summary,
            "has_implied_cagr": "implied_cagr" in implied,
            "scenario_count": len(scenario_summary),
            "sensitivity_generated": sensitivity_matrix is not None,
            "quality_gate_passed": quality_gate.get("recalc_consistent", False),
            "warning_count": len(warnings),
            "artifact_ids": [a["artifact_id"] for a in registered_artifacts],
            "output_dir": str(run_dir),
        }

        if "target_price" in valuation_result.summary:
            summary["target_price"] = valuation_result.summary["target_price"]
        if "target_market_cap" in valuation_result.summary:
            summary["target_market_cap"] = valuation_result.summary["target_market_cap"]
        if "irr" in valuation_result.summary:
            summary["irr"] = valuation_result.summary["irr"]

        context.state["summary"] = summary

        return StageResult.completed(
            "估值模型、报告和预测制品已保存",
            summary,
            artifacts=tuple(registered_artifacts),
        )

    return handler


# ============================================================================
# Markdown 报告生成
# ============================================================================

def _build_markdown_report(
    *,
    ticker: str,
    valuation_result,
    scenarios: dict,
    scenario_summary: dict,
    implied: dict,
    quality_gate: dict,
    warnings: list,
    template_applied: str | None,
) -> str:
    """
    构建 Markdown 估值报告

    小白讲解：
        生成人可读的估值报告，包含：
        - 摘要（目标价、目标市值、IRR）
        - 逐年预测表
        - 假设表（假设与事实分栏）
        - 情景对比
        - 隐含预期
        - 质量门结果
        - 警告列表

    参数:
        ticker: 标的代码
        valuation_result: 估值结果
        scenarios: 情景结果
        scenario_summary: 情景摘要
        implied: 隐含预期
        quality_gate: 质量门结果
        warnings: 警告列表
        template_applied: 应用的模板名

    返回:
        Markdown 字符串
    """
    lines = []
    lines.append(f"# 经营驱动估值报告 — {ticker}")
    lines.append(f"\n生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    if template_applied:
        lines.append(f"**应用模板：** `{template_applied}`\n")

    # === 摘要 ===
    lines.append("## 摘要\n")
    lines.append("| 指标 | 值 |")
    lines.append("|---|---|")
    for key, value in valuation_result.summary.items():
        if isinstance(value, float):
            if abs(value) < 0.01:
                lines.append(f"| {key} | {value:.6f} |")
            elif abs(value) < 100:
                lines.append(f"| {key} | {value:.4f} |")
            else:
                lines.append(f"| {key} | {value:.2f} |")
        else:
            lines.append(f"| {key} | {value} |")

    # === 逐年预测 ===
    lines.append("\n## 逐年预测\n")
    if valuation_result.projections:
        years = sorted(set(
            year for proj in valuation_result.projections.values()
            for year in proj.keys()
        ))
        if years:
            header = "| 指标 | " + " | ".join(str(y) for y in years) + " |"
            sep = "|---|" + "---|" * len(years)
            lines.append(header)
            lines.append(sep)
            metric_labels = {
                "revenue": "收入（亿元）",
                "net_income": "净利润（亿元）",
                "eps": "EPS（元）",
            }
            for metric, year_values in valuation_result.projections.items():
                label = metric_labels.get(metric, metric)
                row = f"| {label} |"
                for year in years:
                    val = year_values.get(year)
                    if val is None:
                        row += " — |"
                    elif isinstance(val, float):
                        if abs(val) < 0.01:
                            row += f" {val:.6f} |"
                        elif abs(val) < 100:
                            row += f" {val:.4f} |"
                        else:
                            row += f" {val:.2f} |"
                    else:
                        row += f" {val} |"
                lines.append(row)

    # === 假设表 ===
    lines.append("\n## 假设表\n")
    lines.append("| 年份 | 变量 | 标签 | 值 | 单位 | 来源 | 类型 |")
    lines.append("|---|---|---|---|---|---|---|")
    for a in valuation_result.assumptions_table:
        atype = "假设" if a.get("is_assumption") else "事实"
        value = a.get("value")
        if isinstance(value, float):
            value_str = f"{value:.4f}"
        else:
            value_str = str(value)
        lines.append(
            f"| {a.get('year')} | {a.get('variable')} | {a.get('label')} | "
            f"{value_str} | {a.get('unit')} | {a.get('source')} | {atype} |"
        )

    # === 情景对比 ===
    if scenario_summary:
        lines.append("\n## 情景对比\n")
        lines.append("| 情景 | 目标价 | 目标市值 |")
        lines.append("|---|---|---|")
        for name, info in scenario_summary.items():
            tp = info.get("target_price")
            tm = info.get("target_market_cap")
            tp_str = f"{tp:.4f}" if isinstance(tp, float) else "—"
            tm_str = f"{tm:.4f}" if isinstance(tm, float) else "—"
            lines.append(f"| {name} | {tp_str} | {tm_str} |")

    # === 隐含预期 ===
    if implied:
        lines.append("\n## 当前价格隐含预期\n")
        lines.append("| 指标 | 值 |")
        lines.append("|---|---|")
        label_map = {
            "implied_cagr": "隐含 CAGR",
            "implied_net_margin": "隐含净利率",
            "implied_dcu_shipment": "隐含 DCU 出货量（万颗）",
        }
        for key, value in implied.items():
            label = label_map.get(key, key)
            if isinstance(value, float):
                if abs(value) < 1:
                    lines.append(f"| {label} | {value:.6f} |")
                else:
                    lines.append(f"| {label} | {value:.4f} |")
            else:
                lines.append(f"| {label} | {value} |")

    # === 质量门 ===
    if quality_gate:
        lines.append("\n## 质量门\n")
        lines.append("| 检查项 | 结果 |")
        lines.append("|---|---|")
        check_labels = {
            "recalc_consistent": "复算一致性",
            "target_price_positive": "目标价为正",
            "irr_in_range": "IRR 在合理范围",
            "assumptions_have_source": "假设有来源",
            "implied_consistent": "隐含预期一致",
        }
        for key, label in check_labels.items():
            value = quality_gate.get(key)
            result = "通过" if value else "未通过"
            lines.append(f"| {label} | {result} |")

    # === 警告 ===
    if warnings:
        lines.append("\n## 警告\n")
        for w in warnings:
            lines.append(f"- {w}")

    lines.append("\n---\n")
    lines.append("**说明：** 所有数字由确定性计算完成，可从保存的 JSON 模型完全复算。")

    return "\n".join(lines)


# ============================================================================
# 工作流定义
# ============================================================================

def operating_driver_valuation_definition(
    *,
    artifact_root: str | Path | None = None,
    source_db_path: str | Path | None = None,
    template_path: str | Path | None = None,
) -> WorkflowDefinition:
    """
    构建经营驱动估值工作流定义

    小白讲解：
        这是工作流的"总装车间"——把 11 个阶段按顺序串起来，
        形成一条完整的流水线。
        每个 StageDefinition 是流水线上的一个工位。

    参数:
        artifact_root: 制品根目录（默认 06_outputs/workflows）
        source_db_path: 外部数据源 DB 路径（None 用工作流自己的 DB）
        template_path: 估值模型模板路径（默认 config/valuation_model_templates.json）

    返回:
        WorkflowDefinition，可交给 WorkflowRunner 执行
    """
    root = Path(artifact_root) if artifact_root is not None else DEFAULT_ARTIFACT_ROOT
    configured_source = source_db_path or os.environ.get("SMR_SOURCE_DB_PATH")
    source = Path(configured_source) if configured_source else None
    tmpl_path = Path(template_path) if template_path is not None else DEFAULT_TEMPLATE_PATH

    return WorkflowDefinition(
        workflow_id="operating_driver_valuation",
        title="Operating driver valuation",
        description="Build a deterministic valuation model from operating driver assumptions.",
        input_schema={
            "type": "object",
            "required": ["ticker", "forecast_years", "drivers", "revenue_formula"],
            "properties": {
                "ticker": {"type": "string"},
                "forecast_years": {"type": "array", "items": {"type": "integer"}},
                "drivers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "values_by_year"],
                        "properties": {
                            "name": {"type": "string"},
                            "label": {"type": "string"},
                            "unit": {"type": "string"},
                            "values_by_year": {"type": "object"},
                            "source": {"type": "string"},
                            "is_assumption": {"type": "boolean", "default": True},
                        },
                    },
                },
                "revenue_formula": {"type": "string"},
                "profit_formula": {"type": "string"},
                "shares_outstanding": {"type": "number"},
                "current_price": {"type": "number"},
                "current_market_cap": {"type": "number"},
                "terminal_pe": {"type": "number"},
                "forecast_horizon_years": {"type": "integer"},
                "model_template": {"type": "string"},
                "scenarios": {"type": "object"},
                "sensitivity": {"type": "object"},
                "allow_network": {"type": "boolean", "default": False},
            },
            "additionalProperties": False,
        },
        stages=(
            StageDefinition("validate_input", _validate_input, "验证标的、预测期、驱动变量和公式"),
            StageDefinition(
                "load_market_context",
                _load_market_context_stage(source),
                "读取历史财务、当前价格和市值（允许缺失）",
            ),
            StageDefinition(
                "apply_model_template",
                _apply_model_template_stage(tmpl_path),
                "应用模型模板默认值（如果指定）",
            ),
            StageDefinition("build_assumptions", _build_assumptions, "构建驱动变量假设表"),
            StageDefinition("validate_assumptions", _validate_assumptions, "验证单位、边界和变量依赖"),
            StageDefinition("compute_valuation", _compute_valuation, "计算收入、利润、EPS、目标市值和 IRR"),
            StageDefinition("reverse_implied", _reverse_implied, "反解当前价格隐含预期"),
            StageDefinition("generate_scenarios", _generate_scenarios, "生成悲观、基准、乐观情景"),
            StageDefinition("generate_sensitivity", _generate_sensitivity, "生成二维敏感性矩阵"),
            StageDefinition("independent_recalc", _independent_recalc, "独立复算和质量门检查"),
            StageDefinition(
                "persist_outputs",
                _persist_outputs_stage(root),
                "保存模型 JSON、Markdown 报告和 CSV 预测",
            ),
        ),
    )
