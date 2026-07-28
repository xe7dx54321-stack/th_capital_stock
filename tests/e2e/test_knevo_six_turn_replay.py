"""阶段 14 真实验收契约。

这些测试调用实际生产组件的测试套件，不生成 mock 业务结果。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVAL_CONFIG = PROJECT_ROOT / "config" / "conversation_replay_eval.json"
TOOLS_DIR = PROJECT_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from evaluate_conversation_workflows import WorkflowEvaluator  # noqa: E402


@pytest.fixture(scope="module")
def evaluator() -> WorkflowEvaluator:
    return WorkflowEvaluator(config_path=str(EVAL_CONFIG))


@pytest.fixture(scope="module")
def replay(evaluator: WorkflowEvaluator) -> dict:
    return evaluator.run_six_turn_replay(use_mock=False)


@pytest.fixture(scope="module")
def faults(evaluator: WorkflowEvaluator) -> dict:
    return evaluator.run_fault_injection_suite(use_mock=False)


def test_g0_delivery_contract_is_complete() -> None:
    required = [
        EVAL_CONFIG,
        TOOLS_DIR / "evaluate_conversation_workflows.py",
        Path(__file__),
        PROJECT_ROOT / "docs/runbooks/research-workflow-quality.md",
    ]
    assert all(path.exists() for path in required)
    config = json.loads(EVAL_CONFIG.read_text(encoding="utf-8"))
    assert config["evaluation_policy"]["mock_results_forbidden"] is True
    assert len(config["six_turns"]) == 6
    assert len(config["fault_injections"]) == 11
    assert len(config["acceptance_gates"]) == 12


def test_mock_acceptance_is_explicitly_rejected(evaluator: WorkflowEvaluator) -> None:
    with pytest.raises(ValueError, match="禁止 mock"):
        evaluator.run_six_turn_replay(use_mock=True)
    with pytest.raises(ValueError, match="禁止 mock"):
        evaluator.run_fault_injection_suite(use_mock=True)


def test_g1_six_natural_language_turns_route_to_registered_graphs(replay: dict) -> None:
    assert len(replay["per_turn"]) == 6
    assert replay["all_routed_correctly"], replay["misrouted"]


def test_g2_all_six_real_workflow_suites_pass(replay: dict) -> None:
    assert replay["all_workflows_passed"], replay["workflow_failures"]
    assert replay["core_numerical_errors"] == []


def test_g3_unit_currency_period_and_timing_contracts_pass(replay: dict) -> None:
    assert replay["unit_currency_period_mixups"] == []


def test_g4_and_g7_correction_recomputes_all_four_dependents(replay: dict) -> None:
    assert replay["recalc_coverage"]["total"] == 4
    assert replay["recalc_coverage"]["passed"] == 4
    assert replay["recalc_coverage"]["rate"] == 1.0
    assert replay["missed_downstream_recalcs"] == []


def test_g5_citation_contract_passes(replay: dict) -> None:
    assert replay["citation_coverage"]["rate"] == 1.0
    assert replay["citation_coverage"]["uncited"] == []


def test_g6_memory_governance_contract_passes(replay: dict) -> None:
    assert replay["unapproved_memory_leaks"] == []


def test_g8_all_polymorphic_views_render(replay: dict) -> None:
    assert replay["artifact_coverage"]["rate"] == 1.0
    assert replay["artifact_coverage"]["missing"] == []


def test_g9_to_g10_all_eleven_fault_paths_are_actually_executed(faults: dict) -> None:
    assert len(faults["fault_runs"]) == 11
    assert all(item["verification"]["command"] for item in faults["fault_runs"])
    assert all(not item["crashed"] for item in faults["fault_runs"]), [
        item for item in faults["fault_runs"] if item["crashed"]
    ]
    assert faults["pseudo_precise_conclusions_under_llm_failure"] == []
    assert faults["formal_data_broken_by_firecrawl"] == []


def test_g12_report_boundary_rejects_internal_status_leakage(replay: dict) -> None:
    assert replay["internal_status_leakage_in_report"] == []


def test_g11_skip_is_failure_and_final_pass_cannot_lie(evaluator: WorkflowEvaluator) -> None:
    report = evaluator.final_acceptance_report(skip_check_full=True)
    g11 = next(gate for gate in report["acceptance_gates"] if gate["gate_id"] == "G11")
    assert g11["passed"] is False
    assert report["final_pass"] is False
    assert report["failed_gates"] == ["G11"]
