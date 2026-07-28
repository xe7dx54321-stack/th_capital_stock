from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from smr_app.research.evaluation import (  # noqa: E402
    build_stock_deep_dive_scorecard,
    evaluate_stock_deep_dive_case,
)
from smr_app.runtime.runner import WorkflowRunner  # noqa: E402
from smr_app.workflows.stock_deep_dive import stock_deep_dive_definition  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行个股深度研究 V2 固定十股真实评测。")
    parser.add_argument("--source-db", type=Path, required=True, help="包含真实研究数据的 SQLite 数据库。")
    parser.add_argument(
        "--config", type=Path, default=PROJECT_ROOT / "config" / "stock_deep_dive_v2_eval.json"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "06_outputs" / "evaluations" / "stock_deep_dive_v2",
    )
    parser.add_argument("--fail-on-quality", action="store_true")
    return parser


def _markdown(payload: dict[str, Any]) -> str:
    scorecard = payload["scorecard"]
    lines = [
        "# 个股深度研究 V2 固定十股质量评测",
        "",
        f"- 评测时间：{payload['generated_at']}",
        f"- 样本数量：{scorecard['case_count']}",
        f"- 通过数量：{scorecard['passed_case_count']}",
        f"- 平均得分：{scorecard['average_score']}",
        f"- 研究就绪：{scorecard['research_ready_count']}",
        f"- 证据有限：{scorecard['evidence_limited_count']}",
        f"- 暂无法判断：{scorecard['cannot_conclude_count']}",
        f"- 可检测事实完整性错误：{scorecard['fact_integrity_error_count']}",
        f"- 无依据方向性结论：{scorecard['unsupported_conclusion_count']}",
        f"- 总体结论：{'通过' if scorecard['passed'] else '未通过'}",
        "",
        "| 标的 | 市场 | 样本职责 | 报告状态 | 主张 | 证据 | 隔离字段 | 得分 | 结论 |",
        "|---|---|---|---|---:|---:|---:|---:|---|",
    ]
    for item in payload["results"]:
        lines.append(
            f"| {item['ticker']} | {item['market']} | {item['role']} | {item['report_status']} | "
            f"{item['approved_claim_count']} | {item['usable_evidence_count']} | "
            f"{item['quarantined_field_count']} | {item['score']} | {'通过' if item['passed'] else '未通过'} |"
        )
    lines.extend(["", "## 问题明细", ""])
    any_findings = False
    for item in payload["results"]:
        if not item["findings"]:
            continue
        any_findings = True
        lines.append(f"### {item['ticker']}")
        lines.append("")
        for finding in item["findings"]:
            level = "硬门槛" if finding["hard"] else "体验项"
            lines.append(f"- [{level}] {finding['code']}：{finding['message']}")
        lines.append("")
    if not any_findings:
        lines.append("- 未发现质量问题。")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parser().parse_args()
    source_db = args.source_db.resolve()
    if not source_db.is_file():
        raise SystemExit(f"真实数据源不存在：{source_db}")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    output_dir = args.output_dir.resolve()
    artifacts = output_dir / "artifacts"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    artifacts.mkdir(parents=True, exist_ok=True)
    runner = WorkflowRunner(output_dir / "control.db")
    definition = stock_deep_dive_definition(artifact_root=artifacts, source_db_path=source_db)
    results = []
    for index, case in enumerate(config["cases"], start=1):
        run_id = f"eval_{index:02d}_{case['ticker'].replace('.', '_')}"
        print(f"[{index:02d}/{len(config['cases'])}] {case['ticker']} ...", flush=True)
        run = runner.run(definition, {"ticker": case["ticker"], "allow_network": False}, run_id=run_id)
        run_dir = artifacts / run_id
        packet_path = run_dir / "research_packet.json"
        report_path = run_dir / "stock_deep_dive.md"
        packet = json.loads(packet_path.read_text(encoding="utf-8")) if packet_path.is_file() else None
        report = report_path.read_text(encoding="utf-8") if report_path.is_file() else None
        result = evaluate_stock_deep_dive_case(case=case, run=run, packet=packet, report=report)
        results.append(result)
        print(f"    {'PASS' if result['passed'] else 'FAIL'} score={result['score']}", flush=True)

    payload = {
        "schema_version": "1.0",
        "suite_id": config["suite_id"],
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_db": str(source_db),
        "scorecard": build_stock_deep_dive_scorecard(results),
        "results": results,
    }
    (output_dir / "eval-results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    (output_dir / "eval-report.md").write_text(_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["scorecard"], ensure_ascii=False), flush=True)
    return 1 if args.fail_on_quality and not payload["scorecard"]["passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
