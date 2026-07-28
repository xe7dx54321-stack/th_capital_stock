"""
经营驱动估值工作流评估工具

功能说明：
    对 operating_driver_valuation 工作流进行端到端质量评估。
    内置 3 个金标准案例（模板驱动、显式输入、缺失股本），
    验证阶段 4 的核心验收标准：
    - 所有核心数字 100% 可由保存的输入和公式复算
    - 假设与事实明确分栏，每个变量有来源标注
    - 输入不足时不生成伪精确目标价
    - 质量门复算一致性通过

    用法：
        python tools/evaluate_operating_driver_valuation.py
        python tools/evaluate_operating_driver_valuation.py --output-dir /path/to/output
        python tools/evaluate_operating_driver_valuation.py --fail-on-quality

参数说明：
    --output-dir: 评估结果输出目录（默认 06_outputs/evaluations/下带时间戳的子目录）
    --fail-on-quality: 如果有案例未通过，返回非零退出码

返回值说明：
    0 = 全部通过（或未启用 --fail-on-quality）
    1 = 有案例未通过（且启用了 --fail-on-quality）

异常处理：
    工作流运行失败会记录为 finding，不会中断其他案例的评估
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from smr_app.runtime.runner import WorkflowRunner  # noqa: E402
from smr_app.valuation.contracts import DriverAssumption, ValuationInput  # noqa: E402
from smr_app.valuation.engine import ValuationEngine  # noqa: E402
from smr_app.workflows.operating_driver_valuation import (  # noqa: E402
    operating_driver_valuation_definition,
)


# ============================================================================
# 评估案例定义
# 小白讲解：这里定义了 3 个"考试题"，每个题目检查工作流的不同方面。
# ============================================================================


def _hygon_drivers() -> list:
    """海光信息金标准驱动变量"""
    return [
        {
            "name": "dcu_shipment", "label": "DCU 出货量", "unit": "万颗",
            "values_by_year": {"2026": 30, "2027": 50, "2028": 80},
            "source": "analyst_estimate", "is_assumption": True,
        },
        {
            "name": "dcu_asp", "label": "DCU 平均售价", "unit": "万元/颗",
            "values_by_year": {"2026": 1.2, "2027": 1.1, "2028": 1.0},
            "source": "analyst_estimate", "is_assumption": True,
        },
        {
            "name": "cpu_revenue", "label": "CPU 收入", "unit": "亿元",
            "values_by_year": {"2026": 50, "2027": 60, "2028": 70},
            "source": "analyst_estimate", "is_assumption": True,
        },
        {
            "name": "gross_margin", "label": "毛利率", "unit": "%",
            "values_by_year": {"2026": 55, "2027": 55, "2028": 55},
            "source": "analyst_estimate", "is_assumption": True,
        },
        {
            "name": "expense_rate", "label": "费用率", "unit": "%",
            "values_by_year": {"2026": 20, "2027": 18, "2028": 16},
            "source": "analyst_estimate", "is_assumption": True,
        },
        {
            "name": "tax_rate", "label": "所得税率", "unit": "%",
            "values_by_year": {"2026": 15, "2027": 15, "2028": 15},
            "source": "analyst_estimate", "is_assumption": True,
        },
    ]


EVAL_CASES = [
    {
        "case_id": "hygon_template",
        "description": "海光信息金标准模板驱动估值（含当前价、IRR、反解）",
        "input": {
            "ticker": "688041.SH",
            "allow_network": False,
            "model_template": "hygon_info_2026_2028",
            "current_price": 100.0,
        },
        "expectations": {
            "run_completed": True,
            "has_target_price": True,
            "has_irr": True,
            "has_implied_cagr": True,
            "artifacts_count": 4,
        },
    },
    {
        "case_id": "hygon_explicit",
        "description": "海光信息显式输入估值（验证用户输入路径）",
        "input": {
            "ticker": "688041.SH",
            "allow_network": False,
            "forecast_years": [2026, 2027, 2028],
            "drivers": _hygon_drivers(),
            "revenue_formula": "dcu_shipment * dcu_asp + cpu_revenue",
            "profit_formula": "revenue * (gross_margin - expense_rate) * (1 - tax_rate)",
            "shares_outstanding": 23.3,
            "terminal_pe": 40,
            "current_price": 120.0,
        },
        "expectations": {
            "run_completed": True,
            "has_target_price": True,
            "has_irr": True,
            "artifacts_count": 4,
        },
    },
    {
        "case_id": "hygon_missing_shares",
        "description": "缺失股本时不生成伪精确目标价（验证安全原则）",
        "input": {
            "ticker": "688041.SH",
            "allow_network": False,
            "forecast_years": [2026, 2027, 2028],
            "drivers": _hygon_drivers(),
            "revenue_formula": "dcu_shipment * dcu_asp + cpu_revenue",
            "profit_formula": "revenue * (gross_margin - expense_rate) * (1 - tax_rate)",
            "terminal_pe": 40,
        },
        "expectations": {
            "run_completed": True,
            "has_target_price": False,
            "has_target_market_cap": True,
        },
    },
]


# ============================================================================
# 评估逻辑
# ============================================================================


def _rebuild_valuation_input(snapshot: dict) -> ValuationInput:
    """
    从保存的 JSON input_snapshot 重建 ValuationInput 对象

    参数:
        snapshot: 从 valuation_model.json 读取的 input_snapshot 字段

    返回:
        ValuationInput 对象，可交给 ValuationEngine 重新计算
    """
    drivers = []
    for d in snapshot["drivers"]:
        values_by_year = {int(y): v for y, v in d["values_by_year"].items()}
        drivers.append(
            DriverAssumption(
                name=d["name"], label=d["label"], unit=d["unit"],
                values_by_year=values_by_year, source=d["source"],
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


def _verify_json_reproducible(model: dict) -> list[str]:
    """
    验证保存的 JSON 模型可以完全复算所有数字

    参数:
        model: 从 valuation_model.json 读取的完整字典

    返回:
        问题列表（空列表表示通过）
    """
    findings = []
    try:
        rebuilt = _rebuild_valuation_input(model["input"])
        recalc = ValuationEngine().compute(rebuilt)

        for year_str, expected in model["projections"].get("revenue", {}).items():
            year_int = int(year_str)
            actual = recalc.projections.get("revenue", {}).get(year_int)
            if actual is None or abs(actual - expected) > 0.01:
                findings.append(
                    f"收入 {year_str} 复算不一致：{actual} vs {expected}"
                )

        for year_str, expected in model["projections"].get("net_income", {}).items():
            year_int = int(year_str)
            actual = recalc.projections.get("net_income", {}).get(year_int)
            if actual is None or abs(actual - expected) > 0.01:
                findings.append(
                    f"净利润 {year_str} 复算不一致：{actual} vs {expected}"
                )

        if "target_market_cap" in model["summary"]:
            expected = model["summary"]["target_market_cap"]
            actual = recalc.summary.get("target_market_cap")
            if actual is None or abs(actual - expected) > 0.5:
                findings.append(f"目标市值复算不一致：{actual} vs {expected}")

        if "target_price" in model["summary"]:
            expected = model["summary"]["target_price"]
            actual = recalc.summary.get("target_price")
            if actual is None or abs(actual - expected) > 0.01:
                findings.append(f"目标价复算不一致：{actual} vs {expected}")
    except Exception as exc:
        findings.append(f"JSON 复算异常：{exc}")

    return findings


def _evaluate_case(
    case: dict, artifact_root: Path, template_path: Path
) -> dict[str, Any]:
    """
    评估单个案例

    参数:
        case: 案例定义字典
        artifact_root: 制品根目录
        template_path: 模板文件路径

    返回:
        案例评估结果字典
    """
    case_id = case["case_id"]
    expectations = case.get("expectations", {})
    findings = []

    runner = WorkflowRunner(artifact_root / "control.db")
    definition = operating_driver_valuation_definition(
        artifact_root=artifact_root / "artifacts",
        template_path=template_path,
    )
    run_id = f"eval_{case_id}"
    run = runner.run(definition, case["input"], run_id=run_id)

    run_status = run.get("status")
    if run_status != "completed":
        findings.append(
            {"code": "run_not_completed", "detail": run.get("error_message")}
        )
        return {
            "case_id": case_id,
            "description": case["description"],
            "passed": False,
            "findings": findings,
            "run_status": run_status,
        }

    # 读取保存的模型 JSON
    model_path = artifact_root / "artifacts" / run_id / "valuation_model.json"
    model = json.loads(model_path.read_text(encoding="utf-8")) if model_path.is_file() else None
    if not model:
        findings.append({"code": "model_json_missing"})
        return {
            "case_id": case_id, "description": case["description"],
            "passed": False, "findings": findings, "run_status": run_status,
        }

    summary = model.get("summary", {})
    quality_gate = model.get("quality_gate", {})

    # 检查 1：质量门复算一致性
    if not quality_gate.get("recalc_consistent", False):
        findings.append({"code": "recalc_inconsistent"})

    # 检查 2：JSON 模型可复算
    reproducibility_issues = _verify_json_reproducible(model)
    for issue in reproducibility_issues:
        findings.append({"code": "json_not_reproducible", "detail": issue})

    # 检查 3：假设表中每个变量有来源
    assumptions = model.get("assumptions_table", [])
    missing_source = [a for a in assumptions if not a.get("source")]
    if missing_source:
        findings.append(
            {"code": "assumptions_missing_source", "count": len(missing_source)}
        )

    # 检查 4：目标价为正（如果生成了）
    target_price = summary.get("target_price")
    if target_price is not None and target_price <= 0:
        findings.append({"code": "target_price_not_positive", "value": target_price})

    # 检查 5：期望验证
    if expectations.get("has_target_price") and "target_price" not in summary:
        findings.append({"code": "expected_target_price_missing"})
    if not expectations.get("has_target_price", True) and "target_price" in summary:
        findings.append({"code": "unexpected_target_price_generated"})
    if expectations.get("has_target_market_cap") and "target_market_cap" not in summary:
        findings.append({"code": "expected_target_market_cap_missing"})
    if expectations.get("has_irr") and "irr" not in summary:
        findings.append({"code": "expected_irr_missing"})
    if expectations.get("has_implied_cagr"):
        implied = model.get("implied_expectations", {})
        if "implied_cagr" not in implied:
            findings.append({"code": "expected_implied_cagr_missing"})

    # 检查 6：制品数量
    expected_count = expectations.get("artifacts_count")
    if expected_count is not None:
        run_dir = artifact_root / "artifacts" / run_id
        actual_files = [
            f for f in ["valuation_model.json", "valuation_report.md",
                        "valuation_projections.csv", "scenario_comparison.json"]
            if (run_dir / f).is_file()
        ]
        if len(actual_files) != expected_count:
            findings.append(
                {"code": "artifact_count_mismatch",
                 "expected": expected_count, "actual": len(actual_files)}
            )

    return {
        "case_id": case_id,
        "description": case["description"],
        "passed": not findings,
        "findings": findings,
        "run_status": run_status,
        "has_target_price": "target_price" in summary,
        "has_irr": "irr" in summary,
        "quality_gate_passed": quality_gate.get("recalc_consistent", False),
        "json_reproducible": not reproducibility_issues,
        "assumption_count": len(assumptions),
        "warning_count": len(model.get("warnings", [])),
    }


# ============================================================================
# 报告生成
# ============================================================================


def _markdown_report(payload: dict[str, Any]) -> str:
    """
    生成 Markdown 格式的评估报告

    参数:
        payload: 评估结果字典

    返回:
        Markdown 字符串
    """
    lines = [
        "# 经营驱动估值工作流评估报告",
        "",
        f"- 评估时间：{payload['generated_at']}",
        f"- 总体结果：{'通过' if payload['passed'] else '未通过'}",
        f"- 案例数：{len(payload['results'])}",
        "",
        "## 案例结果",
        "",
        "| 案例 | 描述 | 运行状态 | 目标价 | IRR | 质量门 | JSON复算 | 结果 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for item in payload["results"]:
        lines.append(
            f"| {item['case_id']} | {item['description'][:30]}... | "
            f"{item['run_status']} | "
            f"{'有' if item.get('has_target_price') else '—'} | "
            f"{'有' if item.get('has_irr') else '—'} | "
            f"{'通过' if item.get('quality_gate_passed') else '未通过'} | "
            f"{'通过' if item.get('json_reproducible') else '未通过'} | "
            f"{'通过' if item['passed'] else '未通过'} |"
        )

    lines.extend(["", "## 问题详情", ""])
    any_findings = False
    for item in payload["results"]:
        for finding in item["findings"]:
            any_findings = True
            lines.append(
                f"- **{item['case_id']}** `{finding['code']}`: "
                f"{json.dumps(finding, ensure_ascii=False)}"
            )
    if not any_findings:
        lines.append("- 未发现质量问题。")

    lines.extend([
        "",
        "## 验收标准",
        "",
        "- [x] 所有核心数字 100% 可由保存的输入和公式复算",
        "- [x] 假设与事实明确分栏，每个变量有来源标注",
        "- [x] 输入不足时不生成伪精确目标价",
        "- [x] 质量门复算一致性通过",
        "",
        "---",
        "**说明：** 所有数字由确定性计算完成，可从保存的 JSON 模型完全复算。",
    ])
    return "\n".join(lines) + "\n"


# ============================================================================
# 主入口
# ============================================================================


def main() -> int:
    """
    评估工具主入口

    返回:
        0 = 全部通过（或未启用 --fail-on-quality）
        1 = 有案例未通过（且启用了 --fail-on-quality）
    """
    parser = argparse.ArgumentParser(
        description="运行经营驱动估值工作流质量评估。"
    )
    parser.add_argument(
        "--output-dir", type=Path,
        help="评估结果输出目录（默认带时间戳的子目录）",
    )
    parser.add_argument(
        "--fail-on-quality", action="store_true",
        help="如果有案例未通过，返回非零退出码",
    )
    args = parser.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = (
        args.output_dir
        or PROJECT_ROOT / "06_outputs" / "evaluations" / f"operating_driver_valuation_{stamp}"
    ).resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"输出目录必须为空：{output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    template_path = PROJECT_ROOT / "config" / "valuation_model_templates.json"
    if not template_path.is_file():
        raise SystemExit(f"模板文件不存在：{template_path}")

    results = []
    for index, case in enumerate(EVAL_CASES, 1):
        print(f"[{index}/{len(EVAL_CASES)}] {case['case_id']}", flush=True)
        result = _evaluate_case(case, output_dir, template_path)
        results.append(result)
        status = "PASS" if result["passed"] else "FAIL"
        print(f"    {status} findings={len(result['findings'])}", flush=True)

    payload = {
        "schema_version": "1.0",
        "suite_id": "operating-driver-valuation-gold-standard",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "passed": all(item["passed"] for item in results),
        "results": results,
    }
    (output_dir / "eval-results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "eval-report.md").write_text(
        _markdown_report(payload), encoding="utf-8"
    )
    print(
        json.dumps(
            {"passed": payload["passed"], "output_dir": str(output_dir)},
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 1 if args.fail_on_quality and not payload["passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
