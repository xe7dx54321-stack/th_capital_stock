from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping


@dataclass(frozen=True)
class StageResult:
    status: str
    message: str
    summary: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
    artifacts: tuple[dict[str, Any], ...] = ()

    @classmethod
    def completed(
        cls,
        message: str,
        summary: Mapping[str, Any] | None = None,
        payload: Mapping[str, Any] | None = None,
        artifacts: tuple[dict[str, Any], ...] = (),
    ) -> "StageResult":
        return cls("completed", message, dict(summary or {}), dict(payload or {}), artifacts)

    @classmethod
    def waiting_review(
        cls,
        message: str,
        summary: Mapping[str, Any] | None = None,
        payload: Mapping[str, Any] | None = None,
        artifacts: tuple[dict[str, Any], ...] = (),
    ) -> "StageResult":
        return cls("waiting_review", message, dict(summary or {}), dict(payload or {}), artifacts)


@dataclass
class WorkflowContext:
    run_id: str
    workflow_id: str
    input_data: dict[str, Any]
    db_path: Path
    _request_cancel: Callable[[], None]
    state: dict[str, Any] = field(default_factory=dict)

    def request_cancel(self) -> None:
        self._request_cancel()


StageHandler = Callable[[WorkflowContext], StageResult]


@dataclass(frozen=True)
class StageDefinition:
    stage_id: str
    handler: StageHandler
    title: str | None = None


@dataclass(frozen=True)
class WorkflowDefinition:
    workflow_id: str
    title: str
    description: str
    stages: tuple[StageDefinition, ...] = ()
    input_schema: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    writes_data: bool = True
