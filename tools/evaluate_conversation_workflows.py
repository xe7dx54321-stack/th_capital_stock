"""阶段 14：由真实组件测试提供证据的工作流验收器。

本工具不会构造“全绿”结果。每个结论都来自一个实际执行的 Node、Pytest
或 Vitest 命令；命令失败、超时或硬门槛被跳过都会导致最终验收失败。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_config(config_path: str | None = None) -> dict[str, Any]:
    path = Path(config_path) if config_path else _project_root() / "config" / "conversation_replay_eval.json"
    with path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    if config.get("evaluation_policy", {}).get("mock_results_forbidden") is not True:
        raise ValueError("验收配置必须明确禁止 mock 结果")
    return config


class WorkflowEvaluator:
    """执行六轮回放、十一种故障注入以及十二项硬门槛。"""

    def __init__(self, config_path: str | None = None, verbose: bool = False) -> None:
        self.root = _project_root()
        self.config = _load_config(config_path)
        self.verbose = verbose
        self.six_turns = self.config["six_turns"]
        self.fault_injections = self.config["fault_injections"]
        self.acceptance_gates = self.config["acceptance_gates"]
        self._command_cache: dict[tuple[str, ...], dict[str, Any]] = {}
        self._replay_cache: dict[str, Any] | None = None
        self._fault_cache: dict[str, Any] | None = None

    def _execute(self, command: list[str], timeout_seconds: int = 300) -> dict[str, Any]:
        key = tuple(command)
        if key in self._command_cache:
            return self._command_cache[key]
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=self.root,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
                check=False,
            )
            output = "\n".join(part for part in (completed.stdout, completed.stderr) if part).strip()
            result = {
                "command": command,
                "passed": completed.returncode == 0,
                "exit_code": completed.returncode,
                "duration_seconds": round(time.monotonic() - started, 3),
                "output_tail": output[-4000:],
            }
        except subprocess.TimeoutExpired as error:
            result = {
                "command": command,
                "passed": False,
                "exit_code": None,
                "duration_seconds": round(time.monotonic() - started, 3),
                "output_tail": f"命令超过 {timeout_seconds} 秒：{error}",
            }
        self._command_cache[key] = result
        if self.verbose:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    def _pytest(self, *selectors: str, timeout_seconds: int = 300) -> dict[str, Any]:
        return self._execute(
            [sys.executable, "-m", "pytest", *selectors, "-q", "--tb=short"],
            timeout_seconds=timeout_seconds,
        )

    def _node_test(self, test_file: str, name_pattern: str | None = None) -> dict[str, Any]:
        command = ["node", "--test", "--test-concurrency=1"]
        if name_pattern:
            command.extend(["--test-name-pattern", name_pattern])
        command.append(test_file)
        return self._execute(command)

    def _vitest(self, test_file: str) -> dict[str, Any]:
        npm = shutil.which("npm.cmd") or shutil.which("npm") or "npm.cmd"
        return self._execute(
            [npm, "run", "test:ui", "--", "--run", test_file],
            timeout_seconds=300,
        )

    @staticmethod
    def _failure(command_result: dict[str, Any], category: str) -> list[dict[str, Any]]:
        if command_result["passed"]:
            return []
        return [{
            "category": category,
            "command": command_result["command"],
            "exit_code": command_result["exit_code"],
            "output_tail": command_result["output_tail"],
        }]

    def run_six_turn_replay(self, use_mock: bool = False) -> dict[str, Any]:
        if use_mock:
            raise ValueError("阶段 14 禁止 mock 回放；请执行真实生产组件测试")
        if self._replay_cache is not None:
            return self._replay_cache

        router = self._node_test(
            "tests/api/conversation-task-router-v2.test.js",
            "WorkflowEngine production entry uses Router V2 for the six golden natural-language tasks",
        )
        turn_commands = {
            "pair_switch": self._pytest("tests/workflows/test_pair_switch_decision.py"),
            "operating_valuation": self._pytest("tests/workflows/test_operating_driver_valuation.py"),
            "theme_gap": self._pytest("tests/research/test_theme_expectation_gap.py"),
            "claim_correction": self._pytest("tests/workflows/test_claim_correction_workflow.py"),
            # 该历史测试文件是带退出码的自校验程序，并非 Pytest 用例。
            # 直接执行才能运行其中 37 项断言；Pytest 会以 “0 tests” 退出 5。
            "causal_chain": self._execute(
                [sys.executable, "tests/workflows/test_industry_causal_explainer.py"]
            ),
            "signal_plan": self._pytest("tests/research/test_company_signal_plan.py"),
        }

        per_turn: list[dict[str, Any]] = []
        for turn in self.six_turns:
            execution = turn_commands[turn["verification_id"]]
            per_turn.append({
                "turn_id": turn["turn_id"],
                "name": turn["name"],
                "user_input": turn["user_input"],
                "expected_task_graph": turn["expected_task_graph"],
                "route_correct": router["passed"],
                "workflow_passed": execution["passed"],
                "artifacts_produced": turn["required_artifacts"] if execution["passed"] else [],
                "verification": execution,
            })

        unit_contract = self._pytest(
            "tests/workflows/test_operating_driver_valuation.py::OperatingDriverValuationWorkflowTests::test_percentage_unit_auto_conversion",
            "tests/workflows/test_stock_research_packet_v2.py::ResearchDataNormalizationTests::test_field_provenance_supplies_period_and_rejects_currency_mismatch",
            "tests/workflows/test_stock_research_packet_v2.py::ResearchDataNormalizationTests::test_periodless_conflicting_snapshot_is_quarantined",
        )
        recalc_contract = self._pytest(
            "tests/workflows/test_claim_correction_workflow.py::test_claim_correction_recomputes_every_dependent_claim_and_persists_audit"
        )
        citation_contract = self._node_test("tests/api/citation-validator.test.js")
        memory_contract = self._pytest("tests/test_unified_memory_phase12.py")
        artifact_contract = self._vitest("src/features/artifacts/__tests__/PolymorphicArtifactViews.test.tsx")
        report_boundary = self._node_test(
            "tests/api/stock-research-v3.test.js",
            "V3 validator rejects unknown citations and system metadata",
        )
        artifact_paths = [self.root / item for item in self.config["artifact_views_required_for_g8"]]
        missing_artifact_views = [
            str(path.relative_to(self.root)).replace("\\", "/")
            for path in artifact_paths
            if not path.exists()
        ]

        workflow_failures = [
            {"turn_id": turn["turn_id"], "verification": turn["verification"]}
            for turn in per_turn
            if not turn["workflow_passed"]
        ]
        misrouted = [
            {"turn_id": turn["turn_id"], "expected_task_graph": turn["expected_task_graph"], "router": router}
            for turn in per_turn
            if not turn["route_correct"]
        ]
        produced_types = sorted({
            artifact_type
            for turn in per_turn
            for artifact_type in turn["artifacts_produced"]
        })
        artifact_ok = artifact_contract["passed"] and not missing_artifact_views

        report = {
            "used_mock": False,
            "all_routed_correctly": not misrouted,
            "all_workflows_passed": not workflow_failures,
            "misrouted": misrouted,
            "workflow_failures": workflow_failures,
            "per_turn": per_turn,
            "core_numerical_errors": workflow_failures,
            "unit_currency_period_mixups": self._failure(unit_contract, "unit_currency_period"),
            "recalc_coverage": {
                "rate": 1.0 if recalc_contract["passed"] else 0.0,
                "passed": 4 if recalc_contract["passed"] else 0,
                "total": 4,
                "failed": self._failure(recalc_contract, "dependency_recalculation"),
                "verification": recalc_contract,
            },
            "citation_coverage": {
                "rate": 1.0 if citation_contract["passed"] else 0.0,
                "uncited": self._failure(citation_contract, "citation_contract"),
                "verification": citation_contract,
            },
            "unapproved_memory_leaks": self._failure(memory_contract, "memory_governance"),
            "missed_downstream_recalcs": self._failure(recalc_contract, "dependency_recalculation"),
            "artifact_coverage": {
                "rate": 1.0 if artifact_ok else 0.0,
                "missing": missing_artifact_views,
                "produced_types": produced_types,
                "verification": artifact_contract,
            },
            "internal_status_leakage_in_report": self._failure(report_boundary, "report_boundary"),
            "router_verification": router,
            "unit_verification": unit_contract,
            "memory_verification": memory_contract,
        }
        self._replay_cache = report
        return report

    def run_fault_injection_suite(self, use_mock: bool = False) -> dict[str, Any]:
        if use_mock:
            raise ValueError("阶段 14 禁止 mock 故障注入；请执行真实故障路径测试")
        if self._fault_cache is not None:
            return self._fault_cache

        checks = {
            "llm_unavailable": self._node_test(
                "tests/api/stock-research-v3.test.js",
                "model unavailability keeps a useful governed draft",
            ),
            "firecrawl_unavailable": self._pytest(
                "tests/acquisition/test_firecrawl_provider.py::TestFirecrawlProvider::test_08_transport_error_swallowed"
            ),
            "primary_provider_failure": self._pytest(
                "tests/acquisition/test_szse_provider.py::SzseProviderTests::test_kernel_uses_szse_after_primary_provider_failure"
            ),
            "stale_cache": self._pytest(
                "tests/acquisition/test_kernel.py::AcquisitionKernelTests::test_stale_request_falls_back_and_persists_every_layer"
            ),
            "source_conflict": self._pytest(
                "tests/acquisition/test_kernel.py::AcquisitionKernelTests::test_conflicting_fact_is_quarantined_instead_of_overwriting_verified_fact"
            ),
            "market_calendar_boundary": self._node_test("tests/api/market-calendar.test.js"),
            "unit_currency_period": self._pytest(
                "tests/workflows/test_stock_research_packet_v2.py::ResearchDataNormalizationTests::test_field_provenance_supplies_period_and_rejects_currency_mismatch"
            ),
            "missing_valuation_input": self._pytest(
                "tests/workflows/test_operating_driver_valuation.py::OperatingDriverValuationWorkflowTests::test_missing_shares_no_target_price"
            ),
            "unknown_citation": self._pytest(
                "tests/workflows/test_stock_deep_dive_v3.py::StockDeepDiveV3Tests::test_unknown_citation_is_rejected"
            ),
            "correction_conflict": self._node_test(
                "tests/api/workflow-input-adapters.test.js",
                "claim correction adapter refuses to trust a user value that conflicts with re-fetched data",
            ),
            "session_resume": self._node_test(
                "tests/api/research-session-e2e.test.js",
                "WorkflowEngine saves state after first query and reloads on second engine",
            ),
        }
        fault_runs = []
        for fault in self.fault_injections:
            verification = checks[fault["verification_id"]]
            fault_runs.append({
                **fault,
                "crashed": not verification["passed"],
                "degraded_gracefully": verification["passed"],
                "verification": verification,
            })
        failures = [item for item in fault_runs if item["crashed"]]
        report = {
            "used_mock": False,
            "fault_runs": fault_runs,
            "pseudo_precise_conclusions_under_llm_failure": [
                item for item in failures if item["fault_id"] == "F01"
            ],
            "formal_data_broken_by_firecrawl": [
                item for item in failures if item["fault_id"] in {"F02", "F03"}
            ],
        }
        self._fault_cache = report
        return report

    def _run_check_full(self) -> dict[str, Any]:
        npm = shutil.which("npm.cmd") or shutil.which("npm") or "npm.cmd"
        return self._execute([npm, "run", "check:full"], timeout_seconds=900)

    def final_acceptance_report(
        self,
        use_mock: bool = False,
        skip_check_full: bool = False,
    ) -> dict[str, Any]:
        if use_mock:
            raise ValueError("最终验收禁止 mock")
        replay = self.run_six_turn_replay(use_mock=False)
        faults = self.run_fault_injection_suite(use_mock=False)
        check_full = (
            {
                "passed": False,
                "skipped": True,
                "command": ["npm", "run", "check:full"],
                "output_tail": "硬门槛被跳过，因此 G11 和 final_pass 必须失败。",
            }
            if skip_check_full
            else self._run_check_full()
        )
        gate_values = {
            "G1": replay["all_routed_correctly"],
            "G2": replay["all_workflows_passed"] and not replay["core_numerical_errors"],
            "G3": not replay["unit_currency_period_mixups"],
            "G4": replay["recalc_coverage"]["rate"] == 1.0,
            "G5": replay["citation_coverage"]["rate"] == 1.0,
            "G6": not replay["unapproved_memory_leaks"],
            "G7": not replay["missed_downstream_recalcs"],
            "G8": replay["artifact_coverage"]["rate"] == 1.0,
            "G9": not faults["pseudo_precise_conclusions_under_llm_failure"],
            "G10": not faults["formal_data_broken_by_firecrawl"],
            "G11": check_full["passed"],
            "G12": not replay["internal_status_leakage_in_report"],
        }
        gates = [
            {
                **gate,
                "passed": bool(gate_values[gate["gate_id"]]),
            }
            for gate in self.acceptance_gates
        ]
        deliverable_paths = [
            self.root / "config/conversation_replay_eval.json",
            self.root / "tools/evaluate_conversation_workflows.py",
            self.root / "tests/e2e/test_knevo_six_turn_replay.py",
            self.root / "docs/runbooks/research-workflow-quality.md",
        ]
        deliverables_ok = all(path.exists() for path in deliverable_paths)
        hard_gates_pass = all(gate["passed"] for gate in gates if gate["hard_requirement"])
        summary = {
            "evaluation_mode": "real_component_execution",
            "used_mock": False,
            "skip_check_full": skip_check_full,
            "six_turns_passed": replay["all_routed_correctly"] and replay["all_workflows_passed"],
            "fault_injections_passed": all(not item["crashed"] for item in faults["fault_runs"]),
            "acceptance_gates": gates,
            "deliverables_ok": deliverables_ok,
            "check_full": check_full,
            "failed_gates": [gate["gate_id"] for gate in gates if not gate["passed"]],
            "final_pass": (
                hard_gates_pass
                and deliverables_ok
                and replay["all_routed_correctly"]
                and replay["all_workflows_passed"]
                and all(not item["crashed"] for item in faults["fault_runs"])
            ),
        }
        return summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="阶段 14 真实组件验收器")
    parser.add_argument("mode", choices=("replay", "faults", "final"))
    parser.add_argument("--config", default=None)
    parser.add_argument("--skip-check-full", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="已禁用；提供该参数会失败，以防把模拟结果误报为验收通过。",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.mock:
        print(json.dumps({"error": "mock acceptance is forbidden", "final_pass": False}, ensure_ascii=False))
        return 2
    evaluator = WorkflowEvaluator(config_path=args.config, verbose=args.verbose)
    if args.mode == "replay":
        report = evaluator.run_six_turn_replay()
        passed = report["all_routed_correctly"] and report["all_workflows_passed"]
    elif args.mode == "faults":
        report = evaluator.run_fault_injection_suite()
        passed = all(not item["crashed"] for item in report["fault_runs"])
    else:
        report = evaluator.final_acceptance_report(skip_check_full=args.skip_check_full)
        passed = report["final_pass"]
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
