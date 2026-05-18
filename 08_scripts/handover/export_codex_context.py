#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore[assignment]


LOCAL_TZ = ZoneInfo("Asia/Shanghai") if ZoneInfo else None
ASSISTANT_MIN_CHARS = 220


@dataclass
class MessageRecord:
    index: int
    line_no: int
    timestamp: str
    role: str
    phase: str | None
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export project-relevant Codex thread context into a workspace folder."
    )
    parser.add_argument(
        "--thread",
        action="append",
        dest="threads",
        required=True,
        help="Codex thread id to export. Repeat for multiple threads.",
    )
    parser.add_argument(
        "--codex-home",
        default=str(Path.home() / ".codex"),
        help="Path to Codex home directory. Default: ~/.codex",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to write the export package into.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the output directory if it already exists.",
    )
    return parser.parse_args()


def load_session_index(codex_home: Path) -> dict[str, dict[str, Any]]:
    index_path = codex_home / "session_index.jsonl"
    if not index_path.exists():
        return {}

    result: dict[str, dict[str, Any]] = {}
    with index_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            thread_id = obj.get("id")
            if thread_id:
                result[thread_id] = obj
    return result


def load_state_threads(codex_home: Path) -> dict[str, dict[str, Any]]:
    db_path = codex_home / "state_5.sqlite"
    if not db_path.exists():
        return {}

    result: dict[str, dict[str, Any]] = {}
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            select
              id,
              rollout_path,
              created_at,
              updated_at,
              source,
              model_provider,
              cwd,
              title,
              sandbox_policy,
              approval_mode,
              tokens_used,
              archived,
              cli_version,
              model,
              reasoning_effort
            from threads
            """
        ).fetchall()
    finally:
        conn.close()

    for row in rows:
        result[row["id"]] = dict(row)
    return result


def find_session_file(codex_home: Path, thread_id: str) -> Path:
    matches = sorted((codex_home / "sessions").rglob(f"*{thread_id}.jsonl"))
    if not matches:
        raise FileNotFoundError(f"Could not locate raw session file for thread {thread_id}")
    return matches[-1]


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.rstrip("\n")
            if not line:
                continue
            try:
                yield line_no, json.loads(line)
            except json.JSONDecodeError:
                continue


def parse_iso_timestamp(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def format_ts(value: str | None) -> str:
    parsed = parse_iso_timestamp(value)
    if not parsed:
        return value or ""
    if LOCAL_TZ:
        parsed = parsed.astimezone(LOCAL_TZ)
    return parsed.strftime("%Y-%m-%d %H:%M:%S %Z")


def normalize_message(message: str) -> str:
    return message.replace("\r\n", "\n").strip()


def build_thread_payload(session_path: Path) -> dict[str, Any]:
    session_meta: dict[str, Any] = {}
    user_messages: list[MessageRecord] = []
    assistant_key_messages: list[MessageRecord] = []
    raw_user_count = 0
    raw_agent_count = 0

    for line_no, obj in iter_jsonl(session_path):
        obj_type = obj.get("type")
        if obj_type == "session_meta" and not session_meta:
            session_meta = obj.get("payload", {})
            continue
        if obj_type != "event_msg":
            continue

        payload = obj.get("payload", {})
        payload_type = payload.get("type")
        if payload_type not in {"user_message", "agent_message"}:
            continue

        message = normalize_message(payload.get("message") or "")
        if not message:
            continue

        record = MessageRecord(
            index=0,
            line_no=line_no,
            timestamp=obj.get("timestamp", ""),
            role="user" if payload_type == "user_message" else "assistant",
            phase=payload.get("phase"),
            message=message,
        )

        if record.role == "user":
            raw_user_count += 1
            record.index = raw_user_count
            user_messages.append(record)
            continue

        raw_agent_count += 1
        keep = record.phase != "commentary" or len(record.message) >= ASSISTANT_MIN_CHARS
        if keep:
            record.index = len(assistant_key_messages) + 1
            assistant_key_messages.append(record)

    return {
        "session_meta": session_meta,
        "user_messages": user_messages,
        "assistant_key_messages": assistant_key_messages,
        "raw_user_count": raw_user_count,
        "raw_agent_count": raw_agent_count,
    }


def markdown_quote_block(text: str) -> str:
    return "\n".join(f"> {line}" if line else ">" for line in text.splitlines())


def write_message_log(
    destination: Path,
    heading: str,
    records: list[MessageRecord],
    note: str,
) -> None:
    lines = [f"# {heading}", "", note, ""]
    for record in records:
        phase_note = f" | phase={record.phase}" if record.phase else ""
        lines.append(
            f"## {record.index:03d} | {record.role} | {format_ts(record.timestamp)}{phase_note} | session_line={record.line_no}"
        )
        lines.append("")
        lines.append(markdown_quote_block(record.message))
        lines.append("")
    destination.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def render_thread_overview(
    thread_id: str,
    session_file: Path,
    session_index_row: dict[str, Any] | None,
    state_row: dict[str, Any] | None,
    payload: dict[str, Any],
) -> str:
    session_meta = payload["session_meta"] or {}
    user_messages: list[MessageRecord] = payload["user_messages"]
    assistant_key_messages: list[MessageRecord] = payload["assistant_key_messages"]

    title = (
        (session_index_row or {}).get("thread_name")
        or (state_row or {}).get("title")
        or session_meta.get("id")
        or thread_id
    )

    created_at = session_meta.get("timestamp") or iso_from_unix((state_row or {}).get("created_at"))
    updated_at = iso_from_unix((state_row or {}).get("updated_at")) or (session_index_row or {}).get(
        "updated_at"
    )

    lines = [
        f"# Thread {thread_id}",
        "",
        f"- title: {title}",
        f"- cwd: {(state_row or {}).get('cwd') or session_meta.get('cwd') or ''}",
        f"- source session file: {session_file}",
        f"- created_at: {format_ts(created_at)}",
        f"- updated_at: {format_ts(updated_at)}",
        f"- raw user message count: {payload['raw_user_count']}",
        f"- raw assistant message count: {payload['raw_agent_count']}",
        f"- exported assistant key message count: {len(assistant_key_messages)}",
        "",
    ]

    if user_messages:
        lines.extend(
            [
                "## First User Message",
                "",
                markdown_quote_block(user_messages[0].message),
                "",
            ]
        )
    if assistant_key_messages:
        lines.extend(
            [
                "## Latest Key Assistant Message",
                "",
                markdown_quote_block(assistant_key_messages[-1].message),
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def iso_from_unix(value: Any) -> str | None:
    if value is None or value == "":
        return None
    try:
        stamp = int(value)
    except (TypeError, ValueError):
        return None
    return dt.datetime.fromtimestamp(stamp, tz=dt.timezone.utc).isoformat().replace("+00:00", "Z")


def write_thread_index(destination: Path, entries: list[dict[str, Any]]) -> None:
    lines = [
        "# Codex Thread Index",
        "",
        "Read order recommendation:",
        "1. 019d3c2d-304c-7230-ab6a-f03a2e6df18c",
        "2. 019d6bfb-a30b-7e02-8a5a-05da0cb9cb82",
        "3. 019d7301-00b7-7952-a3b2-535a2836d79d",
        "",
    ]

    for entry in entries:
        lines.extend(
            [
                f"## {entry['thread_id']}",
                "",
                f"- title: {entry['title']}",
                f"- cwd: {entry['cwd']}",
                f"- created_at: {entry['created_at_local']}",
                f"- updated_at: {entry['updated_at_local']}",
                f"- raw session file: {entry['copied_raw_session']}",
                f"- user log: {entry['user_log']}",
                f"- assistant key log: {entry['assistant_log']}",
                f"- overview: {entry['overview_file']}",
                "",
            ]
        )

    destination.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_all_user_messages(destination: Path, entries: list[dict[str, Any]]) -> None:
    lines = [
        "# All User Directives",
        "",
        "This file merges visible user messages from the exported threads in chronological project order.",
        "",
    ]
    for entry in entries:
        lines.extend(
            [
                f"## {entry['thread_id']} | {entry['title']}",
                "",
            ]
        )
        for record in entry["user_records"]:
            lines.append(f"### {record.index:03d} | {format_ts(record.timestamp)}")
            lines.append("")
            lines.append(markdown_quote_block(record.message))
            lines.append("")

    destination.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    codex_home = Path(args.codex_home).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    if output_dir.exists():
        if not args.overwrite:
            raise SystemExit(
                f"Output directory already exists: {output_dir}\n"
                "Use --overwrite to replace it."
            )
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    threads_dir = output_dir / "threads"
    threads_dir.mkdir(parents=True, exist_ok=True)

    session_index = load_session_index(codex_home)
    state_threads = load_state_threads(codex_home)
    export_entries: list[dict[str, Any]] = []

    for thread_id in args.threads:
        session_file = find_session_file(codex_home, thread_id)
        payload = build_thread_payload(session_file)
        session_index_row = session_index.get(thread_id)
        state_row = state_threads.get(thread_id)

        thread_dir = threads_dir / thread_id
        thread_dir.mkdir(parents=True, exist_ok=True)

        copied_raw_session = thread_dir / session_file.name
        shutil.copy2(session_file, copied_raw_session)

        user_log = thread_dir / "user_messages.md"
        assistant_log = thread_dir / "assistant_key_messages.md"
        overview_file = thread_dir / "overview.md"
        meta_file = thread_dir / "thread_meta.json"

        write_message_log(
            user_log,
            f"User Messages | {thread_id}",
            payload["user_messages"],
            "Visible user messages from the raw session, preserved in order.",
        )
        write_message_log(
            assistant_log,
            f"Assistant Key Messages | {thread_id}",
            payload["assistant_key_messages"],
            "Filtered assistant messages. Kept if non-commentary or long enough to carry material project context.",
        )
        overview_file.write_text(
            render_thread_overview(thread_id, session_file, session_index_row, state_row, payload),
            encoding="utf-8",
        )

        meta_payload = {
            "thread_id": thread_id,
            "session_file_source": str(session_file),
            "session_file_copied": str(copied_raw_session),
            "session_index": session_index_row,
            "state_thread": state_row,
            "session_meta": payload["session_meta"],
            "raw_user_message_count": payload["raw_user_count"],
            "raw_assistant_message_count": payload["raw_agent_count"],
            "assistant_key_message_count": len(payload["assistant_key_messages"]),
        }
        meta_file.write_text(
            json.dumps(meta_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        title = (
            (session_index_row or {}).get("thread_name")
            or (state_row or {}).get("title")
            or payload["session_meta"].get("id")
            or thread_id
        )
        created_at = payload["session_meta"].get("timestamp") or iso_from_unix((state_row or {}).get("created_at"))
        updated_at = iso_from_unix((state_row or {}).get("updated_at")) or (session_index_row or {}).get(
            "updated_at"
        )

        export_entries.append(
            {
                "thread_id": thread_id,
                "title": title,
                "cwd": (state_row or {}).get("cwd") or payload["session_meta"].get("cwd") or "",
                "created_at": created_at,
                "updated_at": updated_at,
                "created_at_local": format_ts(created_at),
                "updated_at_local": format_ts(updated_at),
                "copied_raw_session": str(copied_raw_session),
                "user_log": str(user_log),
                "assistant_log": str(assistant_log),
                "overview_file": str(overview_file),
                "meta_file": str(meta_file),
                "user_records": payload["user_messages"],
            }
        )

    write_thread_index(output_dir / "thread_index.md", export_entries)
    write_all_user_messages(output_dir / "all_user_directives.md", export_entries)

    manifest = {
        "generated_at": dt.datetime.now(tz=dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "codex_home": str(codex_home),
        "output_dir": str(output_dir),
        "thread_count": len(export_entries),
        "threads": [
            {
                key: value
                for key, value in entry.items()
                if key not in {"user_records"}
            }
            for entry in export_entries
        ],
    }
    (output_dir / "export_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
