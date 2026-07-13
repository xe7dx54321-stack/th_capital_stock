from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

from .runtime.cancellation import CancellationController
from .runtime.contracts import StageDefinition, StageResult, WorkflowDefinition
from .runtime.event_store import EventStore, utc_now
from .runtime.migrations import apply_migrations
from .runtime.registry import production_registry
from .runtime.runner import WorkflowRunner


DEFAULT_DB_PATH = Path(os.environ.get("SMR_DB_PATH", "01_data/db/smr.db"))


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _test_fixture() -> WorkflowDefinition:
    return WorkflowDefinition(
        workflow_id="test_fixture",
        title="Runtime test fixture",
        description="Local deterministic runtime verification.",
        stages=(
            StageDefinition("prepare", lambda _context: StageResult.completed("Fixture prepared", {"prepared": True})),
            StageDefinition("finish", lambda _context: StageResult.completed("Fixture completed", {"ok": True})),
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m smr_app", description="SMR local workflow runtime")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("list", help="List fixed production workflows")

    run_parser = commands.add_parser("run", help="Run a workflow synchronously")
    run_parser.add_argument("workflow_id")
    run_parser.add_argument("--input", default="{}", help="JSON object")
    run_parser.add_argument("--run-id")
    run_parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)

    status_parser = commands.add_parser("status", help="Show one run and its events")
    status_parser.add_argument("run_id")
    status_parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)

    cancel_parser = commands.add_parser("cancel", help="Request cancellation")
    cancel_parser.add_argument("run_id")
    cancel_parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)

    migrate_parser = commands.add_parser("migrate", help="Apply ordered SQLite migrations")
    migrate_parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    return parser


def _list_workflows() -> int:
    definitions = production_registry().list()
    print(
        _json(
            [
                {
                    "workflow_id": definition.workflow_id,
                    "title": definition.title,
                    "description": definition.description,
                    "enabled": definition.enabled,
                }
                for definition in definitions
            ]
        )
    )
    return 0


def _run_workflow(args: argparse.Namespace) -> int:
    try:
        input_data = json.loads(args.input)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid --input JSON: {exc.msg}") from exc
    if not isinstance(input_data, dict):
        raise ValueError("--input must be a JSON object")
    definition = _test_fixture() if args.workflow_id == "test_fixture" else production_registry().get(args.workflow_id)
    run = WorkflowRunner(args.db_path).run(definition, input_data, run_id=args.run_id)
    print(_json(run))
    return 0 if run["status"] in {"completed", "waiting_review", "cancelled"} else 1


def _status(args: argparse.Namespace) -> int:
    apply_migrations(args.db_path)
    conn = sqlite3.connect(args.db_path)
    try:
        store = EventStore(conn)
        print(_json({"run": store.get_run(args.run_id), "events": store.list_events(args.run_id)}))
    finally:
        conn.close()
    return 0


def _cancel(args: argparse.Namespace) -> int:
    apply_migrations(args.db_path)
    conn = sqlite3.connect(args.db_path)
    try:
        store = EventStore(conn)
        before = store.get_run(args.run_id)
        requested = CancellationController(conn, args.run_id).request()
        if requested and before["status"] == "waiting_review":
            store.update_run(args.run_id, status="cancelled", completed_at=utc_now())
            store.append_event(args.run_id, "run.cancelled", "Run cancelled while waiting for review")
        print(_json({"run_id": args.run_id, "cancel_requested": requested, "status": store.get_run(args.run_id)["status"]}))
    finally:
        conn.close()
    return 0


def _migrate(args: argparse.Namespace) -> int:
    result = apply_migrations(args.db_path)
    print(_json({"applied": result.applied_versions, "skipped": result.skipped_versions, "db_path": str(args.db_path)}))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "list":
            return _list_workflows()
        if args.command == "run":
            return _run_workflow(args)
        if args.command == "status":
            return _status(args)
        if args.command == "cancel":
            return _cancel(args)
        if args.command == "migrate":
            return _migrate(args)
    except (KeyError, RuntimeError, ValueError) as exc:
        print(_json({"error": type(exc).__name__, "message": str(exc)}), file=sys.stderr)
        return 2
    return 2
