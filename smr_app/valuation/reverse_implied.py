"""
反解隐含预期 - 从当前价格反推市场预期

功能说明：
    从当前价格反解市场隐含的增长率、利润率或出货量。
    核心原则：正向模型和反向模型必须一致。

    公式基础：
    - 当前价格 = (基期净利 × (1+g)^n / 股本) × 终值PE
    - 反解 g: g = (当前价 × 股本 / (基期净利 × PE)) ^ (1/n) - 1
    - 反解 margin: margin = 当前价 × 股本 / (收入 × PE)
    - 反解 shipment: shipment = (当前价 × 股本 / PE - CPU收入 × margin) / (ASP × margin)

参数说明：
    solve_implied_cagr(...) - 反解隐含增长率
    solve_implied_margin(...) - 反解隐含利润率
    solve_implied_shipment(...) - 反解隐含出货量

返回值说明：
    返回反解的数值，无效输入返回 None

异常处理：
    无效输入返回 None 而非崩溃
"""

import math


class ReverseImplied:
    """
    反解隐含预期

    小白讲解：
        这是"逆向工程"——已知当前股价 100 元，
        反推市场预期这家公司未来几年增长多快、利润率多少、出货量多少。
        这样就能判断当前价格是否合理，以及市场预期是否过于乐观。
    """

    def solve_implied_cagr(
        self,
        current_price: float,
        shares_outstanding: float,
        terminal_pe: float,
        base_net_income: float,
        forecast_horizon_years: int,
    ) -> float | None:
        """
        反解隐含 CAGR（年复合增长率）

        公式:
            current_price = (base_net_income × (1+g)^n / shares) × PE
            g = (current_price × shares / (base_net_income × PE)) ^ (1/n) - 1

        参数:
            current_price: 当前股价
            shares_outstanding: 股本（亿股）
            terminal_pe: 终值 PE
            base_net_income: 基期净利润（亿元）
            forecast_horizon_years: 预测年限

        返回:
            隐含 CAGR，无效输入返回 None
        """
        if not all([
            current_price and current_price > 0,
            shares_outstanding and shares_outstanding > 0,
            terminal_pe and terminal_pe > 0,
            base_net_income and base_net_income > 0,
            forecast_horizon_years and forecast_horizon_years > 0,
        ]):
            return None

        ratio = (current_price * shares_outstanding) / (base_net_income * terminal_pe)
        if ratio <= 0:
            return None

        cagr = ratio ** (1.0 / forecast_horizon_years) - 1.0
        return cagr

    def solve_implied_margin(
        self,
        current_price: float,
        shares_outstanding: float,
        terminal_pe: float,
        forecast_revenue: float,
    ) -> float | None:
        """
        反解隐含净利率

        公式:
            current_price = (forecast_revenue × margin / shares) × PE
            margin = current_price × shares / (forecast_revenue × PE)

        参数:
            current_price: 当前股价
            shares_outstanding: 股本（亿股）
            terminal_pe: 终值 PE
            forecast_revenue: 预测收入（亿元）

        返回:
            隐含净利率（0-1 之间），无效输入返回 None
        """
        if not all([
            current_price and current_price > 0,
            shares_outstanding and shares_outstanding > 0,
            terminal_pe and terminal_pe > 0,
            forecast_revenue and forecast_revenue > 0,
        ]):
            return None

        margin = (current_price * shares_outstanding) / (forecast_revenue * terminal_pe)
        return margin

    def solve_implied_shipment(
        self,
        current_price: float,
        shares_outstanding: float,
        terminal_pe: float,
        asp: float,
        cpu_revenue: float,
        net_margin: float,
    ) -> float | None:
        """
        反解隐含出货量

        公式:
            current_price = ((shipment × ASP + CPU_revenue) × margin / shares) × PE
            shipment = (current_price × shares / (PE × margin) - CPU_revenue) / ASP

        参数:
            current_price: 当前股价
            shares_outstanding: 股本（亿股）
            terminal_pe: 终值 PE
            asp: 平均售价（万元/颗）
            cpu_revenue: CPU 收入（亿元）
            net_margin: 净利率（0-1 之间）

        返回:
            隐含出货量（万颗），无效输入返回 None
        """
        if not all([
            current_price and current_price > 0,
            shares_outstanding and shares_outstanding > 0,
            terminal_pe and terminal_pe > 0,
            asp and asp > 0,
            net_margin and net_margin > 0,
        ]):
            return None

        # current_price * shares / PE = 隐含净利润
        implied_net_income = (current_price * shares_outstanding) / terminal_pe

        # 隐含收入 = 隐含净利润 / margin
        implied_revenue = implied_net_income / net_margin

        # 隐含 DCU 收入 = 隐含收入 - CPU 收入
        implied_dcu_revenue = implied_revenue - cpu_revenue

        if implied_dcu_revenue <= 0:
            return None

        # 隐含出货量 = DCU 收入 / ASP
        implied_shipment = implied_dcu_revenue / asp
        return implied_shipment
