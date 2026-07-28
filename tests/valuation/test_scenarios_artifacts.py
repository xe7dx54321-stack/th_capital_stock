"""
情景分析和制品生成测试
"""

import pytest
import json
import os
import tempfile


def test_scenario_generator_produces_pessimistic_base_optimistic():
    """测试生成悲观、基准、乐观三种情景"""
    from smr_app.valuation.scenarios import ScenarioGenerator
    from smr_app.valuation.contracts import ValuationInput, DriverAssumption

    gen = ScenarioGenerator()
    base_input = ValuationInput(
        entity_key="688041.SH",
        forecast_years=[2028],
        drivers=[
            DriverAssumption(
                name="dcu_shipment", label="DCU出货量", unit="万颗",
                values_by_year={2028: 80},
                source="estimate", is_assumption=True,
            ),
            DriverAssumption(
                name="dcu_asp", label="DCU平均售价", unit="万元/颗",
                values_by_year={2028: 2.5},
                source="estimate", is_assumption=True,
            ),
            DriverAssumption(
                name="cpu_revenue", label="CPU收入", unit="亿元",
                values_by_year={2028: 50},
                source="estimate", is_assumption=True,
            ),
            DriverAssumption(
                name="net_margin", label="净利率", unit="%",
                values_by_year={2028: 25},
                source="estimate", is_assumption=True,
            ),
        ],
        revenue_formula="dcu_shipment * dcu_asp + cpu_revenue",
        profit_formula="revenue * net_margin",
        shares_outstanding=23.2,
        current_price=100.0,
        current_market_cap=2320.0,
        terminal_pe=35,
    )

    results = gen.generate_scenarios(base_input)

    assert "pessimistic" in results
    assert "base" in results
    assert "optimistic" in results

    # 基准情景的收入应为 80*2.5+50=250
    base_revenue = results["base"].projections["revenue"][2028]
    assert abs(base_revenue - 250.0) < 0.01

    # 悲观情景的收入应为 40*2.0+50=130
    pess_revenue = results["pessimistic"].projections["revenue"][2028]
    assert abs(pess_revenue - 130.0) < 0.01

    # 乐观情景的收入应为 104*2.75+50=336
    opt_revenue = results["optimistic"].projections["revenue"][2028]
    assert abs(opt_revenue - 336.0) < 0.01


def test_sensitivity_matrix_generates_grid():
    """测试二维敏感性矩阵"""
    from smr_app.valuation.scenarios import ScenarioGenerator
    from smr_app.valuation.contracts import ValuationInput, DriverAssumption

    gen = ScenarioGenerator()
    base_input = ValuationInput(
        entity_key="688041.SH",
        forecast_years=[2028],
        drivers=[
            DriverAssumption(
                name="dcu_shipment", label="DCU出货量", unit="万颗",
                values_by_year={2028: 80},
                source="estimate", is_assumption=True,
            ),
            DriverAssumption(
                name="dcu_asp", label="DCU平均售价", unit="万元/颗",
                values_by_year={2028: 2.5},
                source="estimate", is_assumption=True,
            ),
            DriverAssumption(
                name="cpu_revenue", label="CPU收入", unit="亿元",
                values_by_year={2028: 50},
                source="estimate", is_assumption=True,
            ),
            DriverAssumption(
                name="net_margin", label="净利率", unit="%",
                values_by_year={2028: 25},
                source="estimate", is_assumption=True,
            ),
        ],
        revenue_formula="dcu_shipment * dcu_asp + cpu_revenue",
        profit_formula="revenue * net_margin",
        shares_outstanding=23.2,
        current_price=100.0,
        current_market_cap=2320.0,
        terminal_pe=35,
    )

    matrix = gen.generate_sensitivity_matrix(
        base_input,
        x_driver="dcu_shipment",
        x_values=[40, 80, 120],
        y_driver="dcu_asp",
        y_values=[2.0, 2.5, 3.0],
    )

    # 验证 3x3 矩阵
    assert len(matrix) == 3
    for y_val, row in matrix.items():
        assert len(row) == 3
        for x_val, target_price in row.items():
            assert target_price is not None, "目标价不应为 None"


def test_artifact_generator_saves_json_markdown_csv():
    """测试制品生成器保存 JSON、Markdown 和 CSV"""
    from smr_app.valuation.artifacts import ArtifactGenerator
    from smr_app.valuation.engine import ValuationEngine
    from smr_app.valuation.contracts import ValuationInput, DriverAssumption

    engine = ValuationEngine()
    base_input = ValuationInput(
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
        current_price=100.0,
        current_market_cap=2320.0,
        terminal_pe=35,
    )

    result = engine.compute(base_input)
    gen = ArtifactGenerator()

    with tempfile.TemporaryDirectory() as tmpdir:
        paths = gen.save_model(result, tmpdir, "688041.SH")

        assert os.path.exists(paths["json"])
        assert os.path.exists(paths["markdown"])
        assert os.path.exists(paths["csv"])

        # JSON 应可往返复算
        with open(paths["json"], "r", encoding="utf-8") as f:
            saved = json.load(f)
        assert saved["entity_key"] == "688041.SH"
        assert saved["summary"]["target_market_cap"] == result.summary["target_market_cap"]

        # Markdown 应包含标题和摘要
        with open(paths["markdown"], "r", encoding="utf-8") as f:
            md = f.read()
        assert "估值报告" in md
        assert "摘要" in md

        # CSV 应包含数据行
        with open(paths["csv"], "r", encoding="utf-8") as f:
            csv = f.read()
        assert "revenue" in csv
        assert "net_income" in csv
