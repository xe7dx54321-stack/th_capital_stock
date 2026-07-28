from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from smr_app.research.report_v3 import REQUIRED_HEADINGS, validate_stock_research_report_v3  # noqa: E402
from smr_app.runtime.runner import WorkflowRunner  # noqa: E402
from smr_app.workflows.stock_deep_dive import stock_deep_dive_definition  # noqa: E402


CITATION_RE = re.compile(r"\[([A-Za-z0-9][A-Za-z0-9_.:-]{2,127})\]")
SYSTEM_TOKENS = ("执行信息", "任务编号：", "权威研究任务：", "隔离字段数量", "执行步骤：")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行个股深度研究 V3 真实跨行业质量评测。")
    parser.add_argument("--source-db", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "config" / "stock_deep_dive_v3_eval.json")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--fail-on-quality", action="store_true")
    return parser


def _case_result(case: dict[str, Any], run: Any, packet: dict[str, Any] | None, report: str | None) -> dict[str, Any]:
    findings = []
    text = report or ""
    run_status = run.get("status") if isinstance(run, dict) else getattr(run, "status", None)
    if run_status != "completed":
        detail = run.get("error_message") if isinstance(run, dict) else getattr(run, "error_message", None)
        findings.append({"code": "run_not_completed", "detail": detail})
    if not packet or packet.get("workflow_version") != "3.0":
        findings.append({"code": "missing_v3_packet"})
    coverage = (packet or {}).get("research_v3", {}).get("analysis", {}).get("coverage", {}).get("score", 0)
    minimum_characters = 7_000 if coverage >= 0.9 else 6_000 if coverage >= 0.75 else 4_000
    if packet and text:
        validation = validate_stock_research_report_v3(text, packet, minimum_characters=minimum_characters)
        findings.extend(validation["errors"])
    else:
        validation = {"status": "failed", "characters": len(text), "citation_count": 0, "coverage": 0}
    missing = [term for term in case.get("expected_terms", []) if term not in text]
    if missing:
        findings.append({"code": "missing_expected_terms", "terms": missing})
    contamination = [term for term in case.get("forbidden_terms", []) if term in text]
    if contamination:
        findings.append({"code": "cross_company_contamination", "terms": contamination})
    system_noise = [term for term in SYSTEM_TOKENS if term in text]
    if system_noise:
        findings.append({"code": "system_metadata_in_report", "terms": system_noise})
    return {
        "ticker": case["ticker"],
        "role": case["role"],
        "passed": not findings,
        "characters": len(text),
        "sections": sum(heading in text for heading in REQUIRED_HEADINGS),
        "citations": len(set(CITATION_RE.findall(text))),
        "coverage": coverage,
        "company_name": (packet or {}).get("research_v3", {}).get("context", {}).get("identity", {}).get("company_name"),
        "findings": findings,
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 个股深度研究 V3 真实跨行业评测",
        "",
        f"- 评测时间：{payload['generated_at']}",
        f"- 总体结果：{'通过' if payload['passed'] else '未通过'}",
        "",
        "| 标的 | 样本角色 | 公司 | 字符数 | 章节 | 引用 | 覆盖率 | 结果 |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for item in payload["results"]:
        lines.append(
            f"| {item['ticker']} | {item['role']} | {item['company_name'] or '—'} | {item['characters']} | "
            f"{item['sections']}/15 | {item['citations']} | {item['coverage']:.0%} | {'通过' if item['passed'] else '未通过'} |"
        )
    lines.extend(["", "## 问题", ""])
    for item in payload["results"]:
        for finding in item["findings"]:
            lines.append(f"- {item['ticker']}：`{finding['code']}` {json.dumps(finding, ensure_ascii=False)}")
    if all(not item["findings"] for item in payload["results"]):
        lines.append("- 未发现硬门槛问题。")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _parser().parse_args()
    source_db = args.source_db.resolve()
    if not source_db.is_file():
        raise SystemExit(f"真实数据源不存在：{source_db}")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = (args.output_dir or PROJECT_ROOT / "06_outputs" / "evaluations" / f"stock_deep_dive_v3_{stamp}").resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"输出目录必须为空：{output_dir}")
    artifact_root = output_dir / "artifacts"
    artifact_root.mkdir(parents=True, exist_ok=True)
    runner = WorkflowRunner(output_dir / "control.db")
    definition = stock_deep_dive_definition(artifact_root=artifact_root, source_db_path=source_db)
    results = []
    for index, case in enumerate(config["cases"], 1):
        run_id = f"v3_eval_{index:02d}_{case['ticker'].replace('.', '_')}"
        print(f"[{index}/{len(config['cases'])}] {case['ticker']}", flush=True)
        run = runner.run(definition, {"ticker": case["ticker"], "allow_network": False}, run_id=run_id)
        run_dir = artifact_root / run_id
        packet_path = run_dir / "research_packet.json"
        report_path = run_dir / "stock_deep_dive.md"
        packet = json.loads(packet_path.read_text(encoding="utf-8")) if packet_path.is_file() else None
        report = report_path.read_text(encoding="utf-8") if report_path.is_file() else None
        result = _case_result(case, run, packet, report)
        results.append(result)
        print(f"    {'PASS' if result['passed'] else 'FAIL'} chars={result['characters']} coverage={result['coverage']:.0%}", flush=True)
    payload = {
        "schema_version": "1.0",
        "suite_id": config["suite_id"],
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_db": str(source_db),
        "passed": all(item["passed"] for item in results),
        "results": results,
    }
    (output_dir / "eval-results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "eval-report.md").write_text(_markdown(payload), encoding="utf-8")
    print(json.dumps({"passed": payload["passed"], "output_dir": str(output_dir)}, ensure_ascii=False), flush=True)
    return 1 if args.fail_on_quality and not payload["passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
