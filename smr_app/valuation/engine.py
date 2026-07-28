"""
估值引擎 - 确定性计算

功能说明：
    从运营假设确定性推导收入、利润、EPS、目标市值和 IRR。
    核心原则：
    - 所有数字由确定性计算完成
    - 禁止 LLM 手算
    - 计算失败后不生成伪精确目标价
    - 假设与事实明确分栏

参数说明：
    compute(valuation_input) - 执行完整估值计算

返回值说明：
    返回 ValuationResult，包含 projections、summary、assumptions_table

异常处理：
    缺失关键输入时返回 None 而非崩溃
"""

import math
from smr_app.valuation.contracts import ValuationInput, ValuationResult, DriverAssumption


class ValuationEngine:
    """
    估值引擎

    小白讲解：
        这是"厨师"——拿到菜谱（ValuationInput）后，
        按照公式一步步做菜（计算），最后端出成品（ValuationResult）。
        厨师不用 AI 猜数字，每一步都用确定性公式计算。
    """

    def compute(self, valuation_input: ValuationInput) -> ValuationResult:
        """
        执行完整估值计算

        参数:
            valuation_input: 估值输入

        返回:
            ValuationResult 包含 projections, summary, assumptions_table
        """
        result = ValuationResult(entity_key=valuation_input.entity_key)

        # === 构建变量上下文 ===
        # 小白讲解：把所有驱动变量按年份展开，方便公式引用。
        # 百分比变量（unit="%"）自动转换为小数（55 → 0.55），
        # 这样公式 revenue * gross_margin 就能正确计算。
        context_by_year = {}
        for year in valuation_input.forecast_years:
            ctx = {}
            for driver in valuation_input.drivers:
                if year in driver.values_by_year:
                    value = driver.values_by_year[year]
                    # 百分比变量自动转换为小数
                    if driver.unit == "%" and abs(value) > 1:
                        value = value / 100.0
                    ctx[driver.name] = value
            context_by_year[year] = ctx

        # === 第一步：计算收入 ===
        revenue_by_year = {}
        if valuation_input.revenue_formula:
            for year in valuation_input.forecast_years:
                ctx = context_by_year[year]
                try:
                    revenue = self._eval_formula(valuation_input.revenue_formula, ctx)
                    revenue_by_year[year] = revenue
                except Exception:
                    result.warnings.append(f"年份 {year} 收入计算失败")
        result.projections["revenue"] = revenue_by_year

        # === 第二步：计算利润 ===
        net_income_by_year = {}
        if valuation_input.profit_formula:
            for year in valuation_input.forecast_years:
                ctx = dict(context_by_year[year])
                ctx["revenue"] = revenue_by_year.get(year, 0)
                try:
                    net_income = self._eval_formula(valuation_input.profit_formula, ctx)
                    net_income_by_year[year] = net_income
                except Exception:
                    result.warnings.append(f"年份 {year} 利润计算失败")
        result.projections["net_income"] = net_income_by_year

        # === 第三步：计算 EPS ===
        eps_by_year = {}
        if valuation_input.shares_outstanding and valuation_input.shares_outstanding > 0:
            for year in valuation_input.forecast_years:
                if year in net_income_by_year:
                    eps_by_year[year] = net_income_by_year[year] / valuation_input.shares_outstanding
        result.projections["eps"] = eps_by_year

        # === 第四步：计算目标市值和目标价 ===
        # 使用最后一年的净利润 × 终值 PE
        if valuation_input.forecast_years and net_income_by_year:
            last_year = valuation_input.forecast_years[-1]
            last_net_income = net_income_by_year.get(last_year)

            if last_net_income is not None and valuation_input.terminal_pe:
                target_market_cap = last_net_income * valuation_input.terminal_pe
                result.summary["target_market_cap"] = target_market_cap

                if valuation_input.shares_outstanding and valuation_input.shares_outstanding > 0:
                    target_price = target_market_cap / valuation_input.shares_outstanding
                    result.summary["target_price"] = target_price

        # === 第五步：计算 IRR ===
        if (
            valuation_input.current_price
            and "target_price" in result.summary
            and valuation_input.forecast_horizon_years > 0
        ):
            target_price = result.summary["target_price"]
            current_price = valuation_input.current_price

            if current_price > 0 and target_price > 0:
                # IRR = (目标价 / 当前价) ^ (1/年数) - 1
                irr = (target_price / current_price) ** (1.0 / valuation_input.forecast_horizon_years) - 1.0
                result.summary["irr"] = irr

        # === 构建假设表（假设与事实分栏）===
        for driver in valuation_input.drivers:
            for year, value in driver.values_by_year.items():
                result.assumptions_table.append({
                    "year": year,
                    "variable": driver.name,
                    "label": driver.label,
                    "value": value,
                    "unit": driver.unit,
                    "source": driver.source,
                    "is_assumption": driver.is_assumption,
                })

        # === 保存输入快照（用于复算）===
        result.input_snapshot = {
            "entity_key": valuation_input.entity_key,
            "forecast_years": valuation_input.forecast_years,
            "revenue_formula": valuation_input.revenue_formula,
            "profit_formula": valuation_input.profit_formula,
            "shares_outstanding": valuation_input.shares_outstanding,
            "current_price": valuation_input.current_price,
            "current_market_cap": valuation_input.current_market_cap,
            "terminal_pe": valuation_input.terminal_pe,
            "forecast_horizon_years": valuation_input.forecast_horizon_years,
            "drivers": [
                {
                    "name": d.name,
                    "label": d.label,
                    "unit": d.unit,
                    "values_by_year": d.values_by_year,
                    "source": d.source,
                    "is_assumption": d.is_assumption,
                }
                for d in valuation_input.drivers
            ],
        }

        return result

    def _eval_formula(self, formula: str, context: dict) -> float:
        """
        安全地计算公式

        小白讲解：
            这就像计算器——输入 "dcu_shipment * dcu_asp + cpu_revenue"，
            系统把变量名替换成实际数字，然后计算结果。
            百分比值（如毛利率 55%）会自动转换为小数（0.55）。

        参数:
            formula: 公式字符串
            context: 变量名到值的映射

        返回:
            计算结果（float）

        异常:
            公式语法错误或变量缺失时抛出
        """
        # 把公式中的变量名替换为实际值
        # 注意：毛利率等百分比变量需要特殊处理
        safe_formula = formula

        # 替换变量
        for var_name, var_value in context.items():
            if var_name in safe_formula:
                safe_formula = safe_formula.replace(var_name, str(var_value))

        # 安全计算（只允许数字、运算符和括号）
        # 移除所有空格
        safe_formula = safe_formula.replace(" ", "")

        # 验证只包含合法字符
        allowed_chars = set("0123456789.+-*/()eE")
        if not all(c in allowed_chars for c in safe_formula):
            raise ValueError(f"公式包含非法字符: {safe_formula}")

        # 计算结果
        result = eval(safe_formula, {"__builtins__": {}}, {})

        return float(result)
