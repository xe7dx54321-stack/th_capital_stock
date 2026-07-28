"""
估值引擎确定性计算测试

功能说明：
    测试估值引擎的核心计算逻辑——收入桥、利润桥、EPS、目标市值、IRR。
    核心原则：所有数字由确定性计算完成，禁止 LLM 手算。

参数说明：
    无直接参数，通过构造假设表和调用引擎验证

返回值说明：
    所有测试应通过，证明计算引擎可独立复算

异常处理：
    测试失败会抛出 AssertionError
"""

import pytest
from datetime import date


def test_engine_computes_revenue_bridge_from_drivers():
    """测试从驱动变量计算收入桥"""
    from smr_app.valuation.engine import ValuationEngine
    from smr_app.valuation.contracts import ValuationInput, DriverAssumption

    # 海光信息示例：DCU 出货量 × ASP + CPU 收入
    engine = ValuationEngine()
    valuation_input = ValuationInput(
        entity_key="688041.SH",
        forecast_years=[2026, 2027, 2028],
        drivers=[
            DriverAssumption(
                name="dcu_shipment",
                label="DCU出货量",
                unit="万颗",
                values_by_year={2026: 30, 2027: 50, 2028: 80},
                source="analyst_estimate",
                is_assumption=True,
            ),
            DriverAssumption(
                name="dcu_asp",
                label="DCU平均售价",
                unit="万元/颗",
                values_by_year={2026: 3.0, 2027: 2.8, 2028: 2.5},
                source="analyst_estimate",
                is_assumption=True,
            ),
            DriverAssumption(
                name="cpu_revenue",
                label="CPU收入",
                unit="亿元",
                values_by_year={2026: 40, 2027: 45, 2028: 50},
                source="analyst_estimate",
                is_assumption=True,
            ),
        ],
        revenue_formula="dcu_shipment * dcu_asp + cpu_revenue",
        shares_outstanding=23.2,  # 亿股
        current_price=120.0,  # 元
        current_market_cap=2784.0,  # 亿元
        terminal_pe=35,
    )

    result = engine.compute(valuation_input)

    # 验证收入计算
    # 2026: 30 * 3.0 + 40 = 130 亿元
    assert "revenue" in result.projections
    assert abs(result.projections["revenue"][2026] - 130.0) < 0.01
    # 2027: 50 * 2.8 + 45 = 185 亿元
    assert abs(result.projections["revenue"][2027] - 185.0) < 0.01
    # 2028: 80 * 2.5 + 50 = 250 亿元
    assert abs(result.projections["revenue"][2028] - 250.0) < 0.01


def test_engine_computes_profit_bridge_from_margins():
    """测试从利润率计算利润桥"""
    from smr_app.valuation.engine import ValuationEngine
    from smr_app.valuation.contracts import ValuationInput, DriverAssumption

    engine = ValuationEngine()
    valuation_input = ValuationInput(
        entity_key="688041.SH",
        forecast_years=[2026, 2027, 2028],
        drivers=[
            DriverAssumption(
                name="dcu_shipment", label="DCU出货量", unit="万颗",
                values_by_year={2026: 30, 2027: 50, 2028: 80},
                source="estimate", is_assumption=True,
            ),
            DriverAssumption(
                name="dcu_asp", label="DCU平均售价", unit="万元/颗",
                values_by_year={2026: 3.0, 2027: 2.8, 2028: 2.5},
                source="estimate", is_assumption=True,
            ),
            DriverAssumption(
                name="cpu_revenue", label="CPU收入", unit="亿元",
                values_by_year={2026: 40, 2027: 45, 2028: 50},
                source="estimate", is_assumption=True,
            ),
            DriverAssumption(
                name="gross_margin", label="毛利率", unit="%",
                values_by_year={2026: 55, 2027: 53, 2028: 50},
                source="estimate", is_assumption=True,
            ),
            DriverAssumption(
                name="expense_rate", label="费用率", unit="%",
                values_by_year={2026: 20, 2027: 18, 2028: 16},
                source="estimate", is_assumption=True,
            ),
            DriverAssumption(
                name="tax_rate", label="所得税率", unit="%",
                values_by_year={2026: 15, 2027: 15, 2028: 15},
                source="estimate", is_assumption=True,
            ),
        ],
        revenue_formula="dcu_shipment * dcu_asp + cpu_revenue",
        profit_formula="revenue * (gross_margin - expense_rate) * (1 - tax_rate)",
        shares_outstanding=23.2,
        current_price=120.0,
        current_market_cap=2784.0,
        terminal_pe=35,
    )

    result = engine.compute(valuation_input)

    # 验证净利润
    # 2026: 130 * (0.55 - 0.20) * (1 - 0.15) = 130 * 0.35 * 0.85 = 38.675 亿元
    assert "net_income" in result.projections
    assert abs(result.projections["net_income"][2026] - 38.675) < 0.01


def test_engine_computes_eps_and_target_market_cap():
    """测试 EPS 和目标市值计算"""
    from smr_app.valuation.engine import ValuationEngine
    from smr_app.valuation.contracts import ValuationInput, DriverAssumption

    engine = ValuationEngine()
    valuation_input = ValuationInput(
        entity_key="688041.SH",
        forecast_years=[2028],
        drivers=[
            DriverAssumption(
                name="revenue", label="收入", unit="亿元",
                values_by_year={2028: 250},
                source="estimate", is_assumption=True,
            ),
            DriverAssumption(
                name="net_margin", label="净利率", unit="%",
                values_by_year={2028: 25},
                source="estimate", is_assumption=True,
            ),
        ],
        revenue_formula="revenue",
        profit_formula="revenue * net_margin",
        shares_outstanding=23.2,
        current_price=120.0,
        current_market_cap=2784.0,
        terminal_pe=35,
    )

    result = engine.compute(valuation_input)

    # EPS = 净利润 / 股本
    # 2028: 250 * 0.25 = 62.5 亿净利 / 23.2 亿股 = 2.698 元/股
    assert "eps" in result.projections
    assert abs(result.projections["eps"][2028] - 62.5 / 23.2) < 0.001

    # 目标市值 = EPS * PE * 股本
    # = 2.698 * 35 * 23.2 = 2189.5 亿元
    assert "target_market_cap" in result.summary
    target_cap = result.summary["target_market_cap"]
    expected = (62.5 / 23.2) * 35 * 23.2  # = 62.5 * 35 = 2187.5
    assert abs(target_cap - expected) < 1.0

    # 目标价 = 目标市值 / 股本
    assert "target_price" in result.summary
    expected_price = expected / 23.2
    assert abs(result.summary["target_price"] - expected_price) < 0.01


def test_engine_computes_irr():
    """测试 IRR（内部收益率）计算"""
    from smr_app.valuation.engine import ValuationEngine
    from smr_app.valuation.contracts import ValuationInput, DriverAssumption

    engine = ValuationEngine()
    valuation_input = ValuationInput(
        entity_key="688041.SH",
        forecast_years=[2028],
        drivers=[
            DriverAssumption(
                name="revenue", label="收入", unit="亿元",
                values_by_year={2028: 250},
                source="estimate", is_assumption=True,
            ),
            DriverAssumption(
                name="net_margin", label="净利率", unit="%",
                values_by_year={2028: 25},
                source="estimate", is_assumption=True,
            ),
        ],
        revenue_formula="revenue",
        profit_formula="revenue * net_margin",
        shares_outstanding=23.2,
        current_price=100.0,  # 当前价 100 元
        current_market_cap=2320.0,
        terminal_pe=35,
        forecast_horizon_years=2,  # 2 年到达终值
    )

    result = engine.compute(valuation_input)

    # 目标价 = 62.5 * 35 / 23.2 = 94.18 元
    # IRR = (目标价 / 当前价) ^ (1/年数) - 1
    # = (94.18 / 100) ^ 0.5 - 1
    # 如果目标价 < 当前价，IRR 为负
    assert "irr" in result.summary
    assert isinstance(result.summary["irr"], (int, float))


def test_engine_rejects_missing_shares():
    """测试缺失股本时不生成伪精确目标价"""
    from smr_app.valuation.engine import ValuationEngine
    from smr_app.valuation.contracts import ValuationInput, DriverAssumption

    engine = ValuationEngine()
    valuation_input = ValuationInput(
        entity_key="688041.SH",
        forecast_years=[2028],
        drivers=[
            DriverAssumption(
                name="revenue", label="收入", unit="亿元",
                values_by_year={2028: 250},
                source="estimate", is_assumption=True,
            ),
        ],
        revenue_formula="revenue",
        profit_formula="revenue * 0.25",
        shares_outstanding=None,  # 缺失
        current_price=100.0,
        current_market_cap=2320.0,
        terminal_pe=35,
    )

    result = engine.compute(valuation_input)

    # 不应生成 EPS 和目标价
    assert "eps" not in result.projections or result.projections.get("eps", {}).get(2028) is None
    assert result.summary.get("target_price") is None
    assert result.summary.get("target_market_cap") is not None  # 市值可以算


def test_engine_handles_zero_or_negative_profit():
    """测试零/负利润时不崩溃"""
    from smr_app.valuation.engine import ValuationEngine
    from smr_app.valuation.contracts import ValuationInput, DriverAssumption

    engine = ValuationEngine()
    valuation_input = ValuationInput(
        entity_key="688041.SH",
        forecast_years=[2026],
        drivers=[
            DriverAssumption(
                name="revenue", label="收入", unit="亿元",
                values_by_year={2026: 100},
                source="estimate", is_assumption=True,
            ),
            DriverAssumption(
                name="net_margin", label="净利率", unit="%",
                values_by_year={2026: -10},  # 亏损
                source="estimate", is_assumption=True,
            ),
        ],
        revenue_formula="revenue",
        profit_formula="revenue * net_margin",
        shares_outstanding=23.2,
        current_price=100.0,
        current_market_cap=2320.0,
        terminal_pe=35,
    )

    result = engine.compute(valuation_input)

    # 负利润应正常计算，不崩溃
    assert result.projections["net_income"][2026] == -10.0  # 100 * (-0.10)
    assert result.projections["eps"][2026] < 0  # 负 EPS
