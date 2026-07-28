"""
反解隐含预期测试

功能说明：
    测试从当前价格反解市场隐含的增长率、利润率或出货量。
    核心原则：正向模型和反向模型必须一致。

参数说明：
    无直接参数，通过构造输入和调用反解器验证

返回值说明：
    所有测试应通过

异常处理：
    测试失败会抛出 AssertionError
"""

import pytest


def test_reverse_implied_solves_cagr_from_current_price():
    """测试从当前价格反解隐含 CAGR"""
    from smr_app.valuation.reverse_implied import ReverseImplied
    from smr_app.valuation.contracts import ValuationInput, DriverAssumption

    ri = ReverseImplied()

    # 假设海光当前 100 元，PE 35x，2025 净利 30 亿，股本 23.2 亿
    # 目标价 = 100 = (30 * (1+g)^2 / 23.2) * 35
    # (1+g)^2 = 100 * 23.2 / (30 * 35) = 2320 / 1050 = 2.2095
    # g = 2.2095^0.5 - 1 = 0.4863
    inputs = {
        "current_price": 100.0,
        "shares_outstanding": 23.2,
        "terminal_pe": 35,
        "base_net_income": 30.0,
        "forecast_horizon_years": 2,
    }

    implied_cagr = ri.solve_implied_cagr(**inputs)

    # 验证：用反解的 CAGR 正向计算应得到当前价
    forward_price = (30.0 * (1 + implied_cagr) ** 2 / 23.2) * 35
    assert abs(forward_price - 100.0) < 0.5, \
        f"反解的 CAGR {implied_cagr} 正向计算得到 {forward_price}，应为 100"


def test_reverse_implied_solves_margin_from_current_price():
    """测试从当前价格反解隐含利润率"""
    from smr_app.valuation.reverse_implied import ReverseImplied

    ri = ReverseImplied()

    inputs = {
        "current_price": 100.0,
        "shares_outstanding": 23.2,
        "terminal_pe": 35,
        "forecast_revenue": 250.0,  # 预测收入
    }

    implied_margin = ri.solve_implied_margin(**inputs)

    # 验证：用反解的利润率正向计算应得到当前价
    forward_net_income = 250.0 * implied_margin
    forward_price = (forward_net_income / 23.2) * 35
    assert abs(forward_price - 100.0) < 0.5, \
        f"反解的利润率 {implied_margin} 正向计算得到 {forward_price}，应为 100"


def test_reverse_implied_solves_shipment_from_current_price():
    """测试从当前价格反解隐含出货量"""
    from smr_app.valuation.reverse_implied import ReverseImplied

    ri = ReverseImplied()

    inputs = {
        "current_price": 100.0,
        "shares_outstanding": 23.2,
        "terminal_pe": 35,
        "asp": 2.5,  # 万元/颗
        "cpu_revenue": 50.0,  # 亿元
        "net_margin": 0.25,
    }

    implied_shipment = ri.solve_implied_shipment(**inputs)

    # 验证：用反解的出货量正向计算应得到当前价
    revenue = implied_shipment * 2.5 + 50.0
    net_income = revenue * 0.25
    forward_price = (net_income / 23.2) * 35
    assert abs(forward_price - 100.0) < 0.5, \
        f"反解的出货量 {implied_shipment} 正向计算得到 {forward_price}，应为 100"


def test_reverse_implied_returns_none_for_invalid_inputs():
    """测试无效输入时返回 None 而不是崩溃"""
    from smr_app.valuation.reverse_implied import ReverseImplied

    ri = ReverseImplied()

    # 缺失关键参数
    result = ri.solve_implied_cagr(
        current_price=0,  # 无效
        shares_outstanding=23.2,
        terminal_pe=35,
        base_net_income=30.0,
        forecast_horizon_years=2,
    )
    assert result is None, "价格为 0 时应返回 None"
