"""
经营驱动估值工作流单元测试

功能说明：
    测试 operating_driver_valuation 工作流的 11 个阶段，覆盖 master plan 阶段 4
    要求的全部场景：收入桥、利润桥、EPS、PE 目标价、反解隐含预期、
    单位换算、零/负利润、极端假设、缺失股本、敏感性矩阵单调性、
    JSON 模型完全可复算、模板补充、用户输入优先级、质量门复算一致性。

    核心原则：所有数字由确定性计算完成，可从保存的 JSON 完全复算。

参数说明：
    无直接参数，通过 WorkflowRunner 运行工作流并验证输出

返回值说明：
    所有测试应通过，证明工作流可正确串联估值引擎、反解器、情景生成器

异常处理：
    测试失败会抛出 AssertionError
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from smr_app.runtime.runner import WorkflowRunner
from smr_app.valuation.contracts import DriverAssumption, ValuationInput
from smr_app.valuation.engine import ValuationEngine
from smr_app.workflows.operating_driver_valuation import (
    operating_driver_valuation_definition,
)


# ============================================================================
# 海光信息金标准测试数据
# 小白讲解：这是测试用的"标准答案"输入，对应模板中的 hygon_info_2026_2028。
# 所有驱动变量、公式、股本、PE 都有明确数值，可以手动验算。
# ============================================================================

HYGON_DRIVERS = [
    {
        "name": "dcu_shipment",
        "label": "DCU 出货量",
        "unit": "万颗",
        "values_by_year": {"2026": 30, "2027": 50, "2028": 80},
        "source": "analyst_estimate",
        "is_assumption": True,
    },
    {
        "name": "dcu_asp",
        "label": "DCU 平均售价",
        "unit": "万元/颗",
        "values_by_year": {"2026": 1.2, "2027": 1.1, "2028": 1.0},
        "source": "analyst_estimate",
        "is_assumption": True,
    },
    {
        "name": "cpu_revenue",
        "label": "CPU 收入",
        "unit": "亿元",
        "values_by_year": {"2026": 50, "2027": 60, "2028": 70},
        "source": "analyst_estimate",
        "is_assumption": True,
    },
    {
        "name": "gross_margin",
        "label": "毛利率",
        "unit": "%",
        "values_by_year": {"2026": 55, "2027": 55, "2028": 55},
        "source": "analyst_estimate",
        "is_assumption": True,
    },
    {
        "name": "expense_rate",
        "label": "费用率",
        "unit": "%",
        "values_by_year": {"2026": 20, "2027": 18, "2028": 16},
        "source": "analyst_estimate",
        "is_assumption": True,
    },
    {
        "name": "tax_rate",
        "label": "所得税率",
        "unit": "%",
        "values_by_year": {"2026": 15, "2027": 15, "2028": 15},
        "source": "analyst_estimate",
        "is_assumption": True,
    },
]


def _hygon_input(*, current_price=None) -> dict:
    """
    构建海光信息完整工作流输入

    参数:
        current_price: 当前股价（可选，提供后才能算 IRR 和反解隐含预期）

    返回:
        工作流输入字典
    """
    data = {
        "ticker": "688041.SH",
        "allow_network": False,
        "forecast_years": [2026, 2027, 2028],
        "drivers": [dict(d) for d in HYGON_DRIVERS],
        "revenue_formula": "dcu_shipment * dcu_asp + cpu_revenue",
        "profit_formula": "revenue * (gross_margin - expense_rate) * (1 - tax_rate)",
        "shares_outstanding": 23.3,
        "terminal_pe": 40,
    }
    if current_price is not None:
        data["current_price"] = current_price
    return data


def _make_template_file(path: Path) -> None:
    """
    在指定路径创建测试用模板文件

    小白讲解：测试需要独立的模板文件，避免依赖项目配置文件的位置。
    模板内容与 config/valuation_model_templates.json 中的金标准一致。

    参数:
        path: 模板文件路径
    """
    template = {
        "schema_version": "1.0",
        "templates": {
            "hygon_info_2026_2028": {
                "template_name": "海光信息 2026-2028（金标准）",
                "forecast_years": [2026, 2027, 2028],
                "forecast_horizon_years": 3,
                "revenue_formula": "dcu_shipment * dcu_asp + cpu_revenue",
                "profit_formula": "revenue * (gross_margin - expense_rate) * (1 - tax_rate)",
                "shares_outstanding": 23.3,
                "terminal_pe": 40,
                "drivers": [dict(d) for d in HYGON_DRIVERS],
            },
        },
    }
    path.write_text(json.dumps(template, ensure_ascii=False), encoding="utf-8")


def _rebuild_valuation_input(snapshot: dict) -> ValuationInput:
    """
    从保存的 JSON input_snapshot 重建 ValuationInput 对象

    小白讲解：JSON 文件里的数字键都是字符串（如 "2026"），
    但 ValuationEngine 需要整数键（如 2026）。
    这个函数负责把字符串键转回整数，这样才能重新计算。

    参数:
        snapshot: 从 valuation_model.json 读取的 input_snapshot 字段

    返回:
        ValuationInput 对象，可交给 ValuationEngine 重新计算
    """
    drivers = []
    for d in snapshot["drivers"]:
        values_by_year = {
            int(year): value for year, value in d["values_by_year"].items()
        }
        drivers.append(
            DriverAssumption(
                name=d["name"],
                label=d["label"],
                unit=d["unit"],
                values_by_year=values_by_year,
                source=d["source"],
                is_assumption=d["is_assumption"],
            )
        )
    return ValuationInput(
        entity_key=snapshot["entity_key"],
        forecast_years=snapshot["forecast_years"],
        drivers=drivers,
        revenue_formula=snapshot["revenue_formula"],
        profit_formula=snapshot.get("profit_formula"),
        shares_outstanding=snapshot.get("shares_outstanding"),
        current_price=snapshot.get("current_price"),
        current_market_cap=snapshot.get("current_market_cap"),
        terminal_pe=snapshot.get("terminal_pe"),
        forecast_horizon_years=snapshot.get(
            "forecast_horizon_years", len(snapshot["forecast_years"])
        ),
    )


# ============================================================================
# 测试套件
# ============================================================================


class OperatingDriverValuationWorkflowTests(unittest.TestCase):
    """
    经营驱动估值工作流测试套件

    小白讲解：
        这套测试验证工作流的 11 个阶段是否正确工作。
        每个测试用例都会在一个独立的临时目录中运行工作流，
        互不干扰。测试覆盖了金标准数字、边界情况和异常处理。
    """

    def setUp(self) -> None:
        """
        每个测试开始前创建临时目录和模板文件

        小白讲解：每个测试用独立的"沙箱"，测完自动清理。
        """
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.template_path = self.root / "templates.json"
        _make_template_file(self.template_path)

    def tearDown(self) -> None:
        """测试结束后清理临时目录"""
        self._tmp.cleanup()

    def _run(self, input_data: dict, *, run_id: str = "test_run") -> dict:
        """
        运行估值工作流的辅助方法

        参数:
            input_data: 工作流输入字典
            run_id: 运行 ID（用于定位保存的制品）

        返回:
            工作流运行结果字典，包含 status 和 summary
        """
        runner = WorkflowRunner(self.root / "runtime.db")
        definition = operating_driver_valuation_definition(
            artifact_root=self.root / "artifacts",
            template_path=self.template_path,
        )
        return runner.run(definition, input_data, run_id=run_id)

    def _load_model_json(self, run_id: str = "test_run") -> dict:
        """
        读取保存的估值模型 JSON

        参数:
            run_id: 运行 ID

        返回:
            解析后的 JSON 字典
        """
        path = self.root / "artifacts" / run_id / "valuation_model.json"
        return json.loads(path.read_text(encoding="utf-8"))

    # ========================================================================
    # 测试 1：完整工作流完成并保存 4 个制品
    # ========================================================================

    def test_workflow_completes_and_saves_four_artifacts(self):
        """
        验证完整工作流能跑完，且保存 4 个制品文件

        小白讲解：这是最基本的"冒烟测试"——确认整条流水线不会中途崩溃，
        最后产出 JSON、Markdown、CSV、情景对比 4 个文件。
        """
        result = self._run(_hygon_input(current_price=100.0))
        self.assertEqual(result["status"], "completed")

        summary = result["summary"]
        self.assertEqual(summary["ticker"], "688041.SH")
        self.assertTrue(summary["has_target_price"])
        self.assertTrue(summary["has_irr"])
        self.assertEqual(len(summary["artifact_ids"]), 4)

        run_dir = self.root / "artifacts" / "test_run"
        self.assertTrue((run_dir / "valuation_model.json").is_file())
        self.assertTrue((run_dir / "valuation_report.md").is_file())
        self.assertTrue((run_dir / "valuation_projections.csv").is_file())
        self.assertTrue((run_dir / "scenario_comparison.json").is_file())

    # ========================================================================
    # 测试 2：收入桥计算正确
    # ========================================================================

    def test_revenue_bridge_matches_manual_calculation(self):
        """
        验证收入桥（逐年收入）与手动计算一致

        手动计算：
            2026: 30 × 1.2 + 50 = 86 亿元
            2027: 50 × 1.1 + 60 = 115 亿元
            2028: 80 × 1.0 + 70 = 150 亿元
        """
        self._run(_hygon_input())
        model = self._load_model_json()
        revenue = model["projections"]["revenue"]

        self.assertAlmostEqual(revenue["2026"], 86.0, places=2)
        self.assertAlmostEqual(revenue["2027"], 115.0, places=2)
        self.assertAlmostEqual(revenue["2028"], 150.0, places=2)

    # ========================================================================
    # 测试 3：利润桥计算正确（含百分比自动转换）
    # ========================================================================

    def test_profit_bridge_matches_manual_calculation(self):
        """
        验证利润桥（逐年净利润）与手动计算一致

        手动计算（百分比已自动转小数：55% → 0.55）：
            2026: 86 × (0.55 - 0.20) × (1 - 0.15) = 86 × 0.35 × 0.85 = 25.585 亿元
            2027: 115 × (0.55 - 0.18) × (1 - 0.15) = 115 × 0.37 × 0.85 = 36.1675 亿元
            2028: 150 × (0.55 - 0.16) × (1 - 0.15) = 150 × 0.39 × 0.85 = 49.725 亿元
        """
        self._run(_hygon_input())
        model = self._load_model_json()
        net_income = model["projections"]["net_income"]

        self.assertAlmostEqual(net_income["2026"], 25.585, places=2)
        self.assertAlmostEqual(net_income["2027"], 36.1675, places=2)
        self.assertAlmostEqual(net_income["2028"], 49.725, places=2)

    # ========================================================================
    # 测试 4：EPS 和目标价计算正确
    # ========================================================================

    def test_eps_and_target_price_correct(self):
        """
        验证 EPS 和目标价与手动计算一致

        手动计算：
            EPS 2028 = 49.725 / 23.3 ≈ 2.1343 元
            目标市值 = 49.725 × 40 = 1989 亿元
            目标价 = 1989 / 23.3 ≈ 85.32 元
        """
        self._run(_hygon_input())
        model = self._load_model_json()
        eps = model["projections"]["eps"]
        summary = model["summary"]

        self.assertAlmostEqual(eps["2028"], 49.725 / 23.3, places=3)
        self.assertAlmostEqual(summary["target_market_cap"], 1989.0, places=1)
        self.assertAlmostEqual(summary["target_price"], 1989.0 / 23.3, places=2)

    # ========================================================================
    # 测试 5：提供当前价时计算 IRR
    # ========================================================================

    def test_irr_calculated_when_current_price_provided(self):
        """
        验证提供当前价后能计算 IRR

        手动计算：
            目标价 ≈ 85.32 元，当前价 = 100 元，年数 = 3
            IRR = (85.32 / 100) ^ (1/3) - 1 ≈ -0.0516（负数，因为目标价低于当前价）
        """
        result = self._run(_hygon_input(current_price=100.0))
        self.assertIn("irr", result["summary"])
        irr = result["summary"]["irr"]
        self.assertIsInstance(irr, (int, float))
        # 目标价 < 当前价，IRR 应为负
        self.assertLess(irr, 0)

    # ========================================================================
    # 测试 6：反解隐含 CAGR 在合理范围
    # ========================================================================

    def test_reverse_implied_cagr_in_reasonable_range(self):
        """
        验证反解的隐含 CAGR 存在且在合理范围

        小白讲解：当前价 120 元高于目标价 85.32 元，说明市场预期增长更快。
        反解出的 CAGR 应为正数且在合理范围（0% ~ 100%）。

        手动估算：
            基期净利 = 25.585 亿元，当前价 = 120，股本 = 23.3，PE = 40，年数 = 3
            ratio = (120 × 23.3) / (25.585 × 40) ≈ 2.732
            CAGR = 2.732 ^ (1/3) - 1 ≈ 39.7%
        """
        self._run(_hygon_input(current_price=120.0))
        model = self._load_model_json()
        implied = model["implied_expectations"]

        self.assertIn("implied_cagr", implied)
        cagr = implied["implied_cagr"]
        self.assertGreater(cagr, 0.0)
        self.assertLess(cagr, 1.0)

    # ========================================================================
    # 测试 7：百分比单位自动转换
    # ========================================================================

    def test_percentage_unit_auto_conversion(self):
        """
        验证百分比变量（unit="%"）的值自动从小数转成正确的计算值

        小白讲解：用户输入毛利率 55（表示 55%），引擎自动转成 0.55 参与计算。
        如果不转换，55 会被当成 5500%，利润计算会完全错误。
        这里用一个简化的单年模型验证：收入 100，毛利率 50%，费用率 0%，
        税率 0%，利润应该正好是 50（而不是 5000）。
        """
        input_data = {
            "ticker": "000001.SZ",
            "allow_network": False,
            "forecast_years": [2026],
            "drivers": [
                {
                    "name": "revenue",
                    "label": "收入",
                    "unit": "亿元",
                    "values_by_year": {"2026": 100},
                    "source": "test",
                    "is_assumption": True,
                },
                {
                    "name": "gross_margin",
                    "label": "毛利率",
                    "unit": "%",
                    "values_by_year": {"2026": 50},
                    "source": "test",
                    "is_assumption": True,
                },
                {
                    "name": "expense_rate",
                    "label": "费用率",
                    "unit": "%",
                    "values_by_year": {"2026": 0},
                    "source": "test",
                    "is_assumption": True,
                },
                {
                    "name": "tax_rate",
                    "label": "税率",
                    "unit": "%",
                    "values_by_year": {"2026": 0},
                    "source": "test",
                    "is_assumption": True,
                },
            ],
            "revenue_formula": "revenue",
            "profit_formula": "revenue * (gross_margin - expense_rate) * (1 - tax_rate)",
            "shares_outstanding": 10.0,
            "terminal_pe": 20,
        }
        self._run(input_data)
        model = self._load_model_json()

        # 毛利率 50% → 0.5，利润 = 100 × 0.5 × 1.0 = 50
        self.assertAlmostEqual(
            model["projections"]["net_income"]["2026"], 50.0, places=2
        )

    # ========================================================================
    # 测试 8：零/负利润不崩溃
    # ========================================================================

    def test_negative_profit_does_not_crash(self):
        """
        验证净利率为负时工作流不崩溃，且利润为负值

        小白讲解：公司亏损时净利率是负数，工作流应该正常计算出负利润，
        而不是崩溃。这是"输入不足或异常时不生成伪精确目标价"原则的体现。
        """
        input_data = {
            "ticker": "000001.SZ",
            "allow_network": False,
            "forecast_years": [2026],
            "drivers": [
                {
                    "name": "revenue",
                    "label": "收入",
                    "unit": "亿元",
                    "values_by_year": {"2026": 100},
                    "source": "test",
                    "is_assumption": True,
                },
                {
                    "name": "net_margin",
                    "label": "净利率",
                    "unit": "%",
                    "values_by_year": {"2026": -10},
                    "source": "test",
                    "is_assumption": True,
                },
            ],
            "revenue_formula": "revenue",
            "profit_formula": "revenue * net_margin",
            "shares_outstanding": 10.0,
            "terminal_pe": 20,
        }
        result = self._run(input_data)
        self.assertEqual(result["status"], "completed")

        model = self._load_model_json()
        # 100 × (-0.10) = -10
        self.assertAlmostEqual(
            model["projections"]["net_income"]["2026"], -10.0, places=2
        )
        # 负利润导致目标市值为负，质量门应剔除目标价
        # 小白讲解：目标价为负是不合理的，质量门会把它删掉
        self.assertNotIn("target_price", model["summary"])

    # ========================================================================
    # 测试 9：极端假设不崩溃
    # ========================================================================

    def test_extreme_assumptions_do_not_crash(self):
        """
        验证极端高值假设不崩溃

        小白讲解：出货量 10000 万颗是极端值，工作流应该正常计算，
        不会因为数字太大而崩溃。
        """
        input_data = _hygon_input()
        # 把 DCU 出货量改成极端高值
        input_data["drivers"][0]["values_by_year"] = {
            "2026": 10000,
            "2027": 12000,
            "2028": 15000,
        }
        result = self._run(input_data)
        self.assertEqual(result["status"], "completed")

        model = self._load_model_json()
        # 2028: 15000 × 1.0 + 70 = 15070
        self.assertAlmostEqual(
            model["projections"]["revenue"]["2028"], 15070.0, places=0
        )

    # ========================================================================
    # 测试 10：缺失股本时不生成目标价
    # ========================================================================

    def test_missing_shares_no_target_price(self):
        """
        验证缺失股本时不生成伪精确目标价

        小白讲解：没有股本就无法算 EPS 和目标价（目标价 = 目标市值 / 股本）。
        工作流应该正常完成，但不生成 target_price 字段。
        目标市值仍然可以算（= 净利 × PE），因为它不需要股本。
        """
        input_data = _hygon_input()
        del input_data["shares_outstanding"]
        result = self._run(input_data)
        self.assertEqual(result["status"], "completed")

        model = self._load_model_json()
        self.assertNotIn("target_price", model["summary"])
        self.assertNotIn("irr", model["summary"])
        # 目标市值仍可计算
        self.assertIn("target_market_cap", model["summary"])

    # ========================================================================
    # 测试 11：敏感性矩阵单调性
    # ========================================================================

    def test_sensitivity_matrix_monotonic(self):
        """
        验证敏感性矩阵中目标价随驱动变量单调递增

        小白讲解：固定 ASP 不变，DCU 出货量越大，收入越高，利润越高，
        目标价也应该越高。如果出现"出货量增加但目标价下降"的情况，
        说明计算逻辑有 bug。
        """
        self._run(_hygon_input(current_price=100.0))
        model = self._load_model_json()
        matrix = model["sensitivity_matrix"]
        self.assertIsNotNone(matrix)

        # 取基准 y 行（y_actual = 1.0 → key = "1.0000"）
        y_key = "1.0000"
        self.assertIn(y_key, matrix)
        row = matrix[y_key]

        # 按 x 值从小到大排序，提取非 None 的目标价
        x_items = sorted(row.items(), key=lambda kv: float(kv[0]))
        prices = [v for _, v in x_items if v is not None]
        self.assertGreater(len(prices), 1)

        # 验证目标价随 x（DCU 出货量）单调递增
        for i in range(1, len(prices)):
            self.assertGreaterEqual(
                prices[i],
                prices[i - 1],
                f"敏感性矩阵目标价不单调递增：{prices[i]} < {prices[i - 1]}",
            )

    # ========================================================================
    # 测试 12：JSON 模型完全可复算
    # ========================================================================

    def test_json_model_fully_reproducible(self):
        """
        验证保存的 JSON 模型可以完全复算所有数字

        小白讲解：这是阶段 4 的核心验收标准——保存的 JSON 包含完整输入，
        任何人拿到这个文件都能重新算出完全一样的收入、利润、EPS、目标价。
        如果复算结果不一致，说明保存的输入有缺失或计算有随机性。
        """
        self._run(_hygon_input(current_price=100.0))
        model = self._load_model_json()

        # 从 input_snapshot 重建 ValuationInput
        rebuilt_input = _rebuild_valuation_input(model["input"])

        # 重新计算
        engine = ValuationEngine()
        recalc_result = engine.compute(rebuilt_input)

        # 验证收入一致
        for year_str, expected in model["projections"]["revenue"].items():
            year_int = int(year_str)
            actual = recalc_result.projections["revenue"].get(year_int)
            self.assertAlmostEqual(
                actual, expected, places=4, msg=f"收入 {year_str} 复算不一致"
            )

        # 验证净利润一致
        for year_str, expected in model["projections"]["net_income"].items():
            year_int = int(year_str)
            actual = recalc_result.projections["net_income"].get(year_int)
            self.assertAlmostEqual(
                actual, expected, places=4, msg=f"净利润 {year_str} 复算不一致"
            )

        # 验证目标市值一致
        if "target_market_cap" in model["summary"]:
            self.assertAlmostEqual(
                recalc_result.summary["target_market_cap"],
                model["summary"]["target_market_cap"],
                places=2,
            )

        # 验证目标价一致
        if "target_price" in model["summary"]:
            self.assertAlmostEqual(
                recalc_result.summary["target_price"],
                model["summary"]["target_price"],
                places=4,
            )

    # ========================================================================
    # 测试 13：模板补充缺失字段
    # ========================================================================

    def test_template_supplements_missing_fields(self):
        """
        验证指定 model_template 后，缺失字段从模板补全

        小白讲解：用户只想说"用海光信息金标准模板估值"，不需要手填所有
        驱动变量和公式。工作流应该自动从模板补全，并正常完成计算。
        """
        input_data = {
            "ticker": "688041.SH",
            "allow_network": False,
            "model_template": "hygon_info_2026_2028",
        }
        result = self._run(input_data, run_id="template_run")
        self.assertEqual(result["status"], "completed")

        summary = result["summary"]
        self.assertEqual(summary["template_applied"], "hygon_info_2026_2028")
        self.assertTrue(summary["has_target_price"])

        # 验证模板补全后的收入与金标准一致
        model = self._load_model_json("template_run")
        self.assertAlmostEqual(
            model["projections"]["revenue"]["2026"], 86.0, places=2
        )

    # ========================================================================
    # 测试 14：用户输入优先于模板
    # ========================================================================

    def test_user_input_overrides_template(self):
        """
        验证用户显式提供的驱动变量不会被模板覆盖

        小白讲解：用户说"DCU 出货量 2026 年是 40 万颗"（而非模板默认的 30），
        工作流应该用 40 而不是 30。模板只补充用户没填的字段。
        """
        input_data = {
            "ticker": "688041.SH",
            "allow_network": False,
            "model_template": "hygon_info_2026_2028",
            # 用户只提供 DCU 出货量，其他从模板补
            "drivers": [
                {
                    "name": "dcu_shipment",
                    "label": "DCU 出货量",
                    "unit": "万颗",
                    "values_by_year": {"2026": 40, "2027": 60, "2028": 90},
                    "source": "user_override",
                    "is_assumption": True,
                },
            ],
        }
        result = self._run(input_data, run_id="override_run")
        self.assertEqual(result["status"], "completed")

        model = self._load_model_json("override_run")
        # 2026: 40 × 1.2 + 50 = 98（而非模板默认的 86）
        self.assertAlmostEqual(
            model["projections"]["revenue"]["2026"], 98.0, places=2
        )
        # 2028: 90 × 1.0 + 70 = 160（而非模板默认的 150）
        self.assertAlmostEqual(
            model["projections"]["revenue"]["2028"], 160.0, places=2
        )

    # ========================================================================
    # 测试 15：质量门复算一致性
    # ========================================================================

    def test_quality_gate_recalc_consistent(self):
        """
        验证质量门的复算一致性检查通过

        小白讲解：工作流在第 10 阶段会把输入重新跑一遍，确认两次结果完全一致。
        这是"确定性计算"的核心保证——同一个输入永远得到同一个输出。
        """
        result = self._run(_hygon_input(current_price=100.0))
        self.assertEqual(result["status"], "completed")

        model = self._load_model_json()
        quality_gate = model["quality_gate"]
        self.assertTrue(quality_gate["recalc_consistent"])
        self.assertEqual(len(quality_gate["errors"]), 0)

    # ========================================================================
    # 测试 16：不存在的模板名会触发警告但不崩溃
    # ========================================================================

    def test_nonexistent_template_produces_warning(self):
        """
        验证指定不存在的模板名时，工作流记录警告并尝试继续

        小白讲解：如果用户写错了模板名，工作流不应该崩溃，
        而是记录"模板不存在"的警告。但因为 forecast_years/drivers/
        revenue_formula 都缺失，会在后续阶段抛出 ValueError。
        这验证了模板应用后必填验证逻辑的正确性。
        """
        input_data = {
            "ticker": "688041.SH",
            "allow_network": False,
            "model_template": "nonexistent_template",
        }
        result = self._run(input_data, run_id="bad_template_run")
        # 模板不存在 → 字段未补全 → 阶段 3 抛出 ValueError
        self.assertEqual(result["status"], "failed")

    # ========================================================================
    # 测试 17：allow_network=true 被拒绝
    # ========================================================================

    def test_allow_network_true_rejected(self):
        """
        验证 allow_network=true 被工作流拒绝

        小白讲解：这个工作流是纯确定性计算，不联网取数。
        如果有人传 allow_network=true，应该立即报错。
        """
        input_data = _hygon_input()
        input_data["allow_network"] = True
        result = self._run(input_data, run_id="network_run")
        self.assertEqual(result["status"], "failed")
        self.assertIn("allow_network", result.get("error_message", ""))


if __name__ == "__main__":
    unittest.main()
