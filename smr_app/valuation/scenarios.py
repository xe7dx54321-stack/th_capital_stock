"""
情景分析 - 悲观、基准、乐观和扩展情景

功能说明：
    生成多维情景分析，每个情景调整驱动变量的值。
    核心原则：每个情景都是确定性的，不含随机数。

参数说明：
    generate_scenarios(base_input, adjustments) - 生成情景列表

返回值说明：
    返回 {情景名: ValuationResult} 字典

异常处理：
    无效调整返回空列表
"""

from smr_app.valuation.contracts import ValuationInput, DriverAssumption, ValuationResult
from smr_app.valuation.engine import ValuationEngine


class ScenarioGenerator:
    """
    情景生成器

    小白讲解：
        这是"如果...会怎样"模拟器。
        基准情景用用户给的假设，悲观情景把出货量砍半，
        乐观情景把出货量翻倍。
        每个情景都走完整的估值计算，这样就能看到范围。
    """

    # 默认情景调整比例
    DEFAULT_SCENARIOS = {
        "pessimistic": {
            "dcu_shipment": 0.5,    # 出货量减半
            "dcu_asp": 0.8,         # ASP 降 20%
            "gross_margin": 0.85,   # 毛利率降 15%
        },
        "base": {},  # 基准无调整
        "optimistic": {
            "dcu_shipment": 1.3,    # 出货量增 30%
            "dcu_asp": 1.1,         # ASP 增 10%
            "gross_margin": 1.1,    # 毛利率增 10%
        },
    }

    def generate_scenarios(
        self,
        base_input: ValuationInput,
        scenarios: dict = None,
    ) -> dict:
        """
        生成多个情景的估值结果

        参数:
            base_input: 基准估值输入
            scenarios: 情景调整字典 {情景名: {变量名: 乘数}}

        返回:
            {情景名: ValuationResult} 字典
        """
        if scenarios is None:
            scenarios = self.DEFAULT_SCENARIOS

        engine = ValuationEngine()
        results = {}

        for scenario_name, adjustments in scenarios.items():
            # 调整驱动变量
            adjusted_drivers = []
            for driver in base_input.drivers:
                adjusted_values = {}
                multiplier = adjustments.get(driver.name, 1.0)

                for year, value in driver.values_by_year.items():
                    adjusted_values[year] = value * multiplier

                adjusted_drivers.append(DriverAssumption(
                    name=driver.name,
                    label=driver.label,
                    unit=driver.unit,
                    values_by_year=adjusted_values,
                    source=f"{driver.source} × {multiplier} ({scenario_name})",
                    is_assumption=driver.is_assumption,
                ))

            # 用调整后的驱动变量构建新输入
            adjusted_input = ValuationInput(
                entity_key=base_input.entity_key,
                forecast_years=base_input.forecast_years,
                drivers=adjusted_drivers,
                revenue_formula=base_input.revenue_formula,
                profit_formula=base_input.profit_formula,
                shares_outstanding=base_input.shares_outstanding,
                current_price=base_input.current_price,
                current_market_cap=base_input.current_market_cap,
                terminal_pe=base_input.terminal_pe,
                forecast_horizon_years=base_input.forecast_horizon_years,
            )

            results[scenario_name] = engine.compute(adjusted_input)

        return results

    def generate_sensitivity_matrix(
        self,
        base_input: ValuationInput,
        x_driver: str,
        x_values: list,
        y_driver: str,
        y_values: list,
    ) -> dict:
        """
        生成二维敏感性矩阵

        小白讲解：
            这是"网格搜索"——固定两个变量（如出货量和 ASP），
            每个组合都算一次目标价，看哪个变量影响最大。

        参数:
            base_input: 基准估值输入
            x_driver: X 轴变量名
            x_values: X 轴值列表
            y_driver: Y 轴变量名
            y_values: Y 轴值列表

        返回:
            {y_value: {x_value: target_price}} 二维字典
        """
        engine = ValuationEngine()
        matrix = {}

        for y_val in y_values:
            matrix[y_val] = {}
            for x_val in x_values:
                # 替换 x_driver 和 y_driver 的最后一年的值
                adjusted_drivers = []
                for driver in base_input.drivers:
                    adjusted_values = dict(driver.values_by_year)
                    if driver.name == x_driver and base_input.forecast_years:
                        last_year = base_input.forecast_years[-1]
                        adjusted_values[last_year] = x_val
                    elif driver.name == y_driver and base_input.forecast_years:
                        last_year = base_input.forecast_years[-1]
                        adjusted_values[last_year] = y_val

                    adjusted_drivers.append(DriverAssumption(
                        name=driver.name,
                        label=driver.label,
                        unit=driver.unit,
                        values_by_year=adjusted_values,
                        source=driver.source,
                        is_assumption=driver.is_assumption,
                    ))

                adjusted_input = ValuationInput(
                    entity_key=base_input.entity_key,
                    forecast_years=base_input.forecast_years,
                    drivers=adjusted_drivers,
                    revenue_formula=base_input.revenue_formula,
                    profit_formula=base_input.profit_formula,
                    shares_outstanding=base_input.shares_outstanding,
                    current_price=base_input.current_price,
                    current_market_cap=base_input.current_market_cap,
                    terminal_pe=base_input.terminal_pe,
                    forecast_horizon_years=base_input.forecast_horizon_years,
                )

                result = engine.compute(adjusted_input)
                matrix[y_val][x_val] = result.summary.get("target_price")

        return matrix
