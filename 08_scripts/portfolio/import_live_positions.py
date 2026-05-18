#!/usr/bin/env python3
"""Import validated live positions into the main position table."""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import env_or_project_path, normalize_project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
INTAKE_DIR = env_or_project_path("SMR_PORTFOLIO_INTAKE_DIR", "04_portfolio", "intake")
POSITIONS_DIR = env_or_project_path("SMR_POSITIONS_DIR", "04_portfolio", "positions")


def find_latest_validation_json():
    candidates = [path for path in INTAKE_DIR.glob("*_live_position_validation.json") if path.is_file()]
    if not candidates:
        raise SystemExit("No live position validation json found. Run validate_live_position_intake.py first.")
    return sorted(candidates, key=lambda path: (path.stat().st_mtime, path.name), reverse=True)[0]


def write_position_note(position_path, created_at, row):
    lines = [
        f"# Position: {row['ts_code']}",
        "",
        f"- Imported At: {created_at}",
        f"- Name: {row.get('name') or row['ts_code']}",
        f"- Entry Date: {row.get('entry_date')}",
        f"- Entry Price: {row.get('entry_price')}",
        f"- Shares: {row.get('derived_shares')}",
        f"- Cost: {row.get('derived_cost')}",
        f"- Target Price: {row.get('target_price')}",
        f"- Stop Loss: {row.get('stop_loss')}",
        f"- Thesis: {row.get('thesis')}",
        f"- Size Input Type: {row.get('size_input_type')}",
        f"- Size Input Value: {row.get('size_input_value')}",
        f"- Source Report ID: {row.get('source_report_id') or '-'}",
        f"- Latest Price / Date: {row.get('latest_close')} / {row.get('latest_trade_date') or '-'}",
        "",
        "## Import Warnings",
        "",
    ]
    for item in row.get("warnings") or ["无"]:
        lines.append(f"- {item}")
    position_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_import_report(markdown_path, json_path, created_at, input_rel_path, imported_rows, skipped_rows, dry_run):
    payload = {
        "created_at": created_at,
        "input_rel_path": input_rel_path,
        "dry_run": dry_run,
        "import_count": len(imported_rows),
        "skipped_count": len(skipped_rows),
        "imported_rows": imported_rows,
        "skipped_rows": skipped_rows,
    }
    lines = [
        "# SMR 真实持仓导入批次",
        "",
        f"- created_at: {created_at}",
        f"- input_rel_path: `{input_rel_path}`",
        f"- dry_run: `{dry_run}`",
        f"- import_count: {len(imported_rows)}",
        f"- skipped_count: {len(skipped_rows)}",
        "",
        "## 导入对象",
        "",
    ]
    for row in imported_rows or []:
        lines.append(f"- `{row['ts_code']}` / {row.get('name') or row['ts_code']} / cost=`{row.get('derived_cost')}` / shares=`{row.get('derived_shares')}`")
    if not imported_rows:
        lines.append("- 无")
    lines.extend(["", "## 跳过对象", ""])
    for row in skipped_rows or []:
        lines.append(f"- `{row['ts_code']}` / {row.get('name') or row['ts_code']} / status=`{row.get('validation_status')}`")
    if not skipped_rows:
        lines.append("- 无")
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Import validated live positions into position table")
    parser.add_argument("--input", help="Path to live_position_validation json; defaults to latest")
    parser.add_argument("--execute", action="store_true", help="Actually write into position table; default is dry-run")
    parser.add_argument("--allow-partial", action="store_true", help="Allow importing ready rows while blocked rows still exist")
    args = parser.parse_args()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    input_path = normalize_project_path(args.input) if args.input else find_latest_validation_json()
    if input_path is None or not input_path.exists():
        raise SystemExit("Input live position validation json not found")

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    ready_rows = payload.get("ready_rows") or []
    blocked_rows = payload.get("blocked_rows") or []
    if not ready_rows:
        raise SystemExit("No ready rows available for import")
    if blocked_rows and not args.allow_partial:
        raise SystemExit("Blocked rows still exist. Pass --allow-partial if you want to import only ready rows.")

    conn = sqlite3.connect(DB_PATH)
    open_positions = conn.execute("SELECT COUNT(*) FROM position WHERE status='open'").fetchone()[0]
    if open_positions:
        conn.close()
        raise SystemExit("position 主表当前已有 open 持仓。为避免混入旧状态，当前导入器默认只接受空仓导入。")

    POSITIONS_DIR.mkdir(parents=True, exist_ok=True)
    imports_dir = POSITIONS_DIR / "imports"
    imports_dir.mkdir(parents=True, exist_ok=True)
    batch_id = created_at.replace(":", "").replace(" ", "_")
    markdown_path = imports_dir / f"{batch_id}_live_position_import.md"
    json_path = imports_dir / f"{batch_id}_live_position_import.json"

    if not args.execute:
        write_import_report(
            markdown_path,
            json_path,
            created_at,
            relative_to_project(input_path),
            ready_rows,
            blocked_rows,
            True,
        )
        conn.close()
        log_run(
            "import_live_positions.py",
            "success",
            "live position import dry-run prepared",
            {
                "input_rel_path": relative_to_project(input_path),
                "ready_count": len(ready_rows),
                "blocked_count": len(blocked_rows),
                "markdown_rel_path": relative_to_project(markdown_path),
                "json_rel_path": relative_to_project(json_path),
                "dry_run": True,
            },
        )
        print(f"Dry-run import markdown: {markdown_path}")
        print(f"Dry-run import json: {json_path}")
        print(f"Ready rows: {len(ready_rows)}")
        print(f"Blocked rows: {len(blocked_rows)}")
        return

    imported_rows = []
    for row in ready_rows:
        conn.execute(
            """
            INSERT INTO position
            (ts_code, entry_date, entry_price, shares, cost, target_price, stop_loss, thesis, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open')
            """,
            (
                row["ts_code"],
                row["entry_date"],
                row["entry_price"],
                row["derived_shares"],
                row["derived_cost"],
                row["target_price"],
                row["stop_loss"],
                row["thesis"],
            ),
        )
        note_path = POSITIONS_DIR / f"{row['ts_code'].replace('.', '_')}_{row['entry_date']}.md"
        write_position_note(note_path, created_at, row)
        imported_rows.append({**row, "position_note_rel_path": relative_to_project(note_path)})

    write_import_report(
        markdown_path,
        json_path,
        created_at,
        relative_to_project(input_path),
        imported_rows,
        blocked_rows,
        False,
    )
    register_snapshot(
        conn,
        entity_type="portfolio_position_import_batch",
        entity_id=created_at[:10],
        status="imported",
        source="import_live_positions.py",
        relationships={
            "input_rel_path": relative_to_project(input_path),
            "markdown_rel_path": relative_to_project(markdown_path),
            "json_rel_path": relative_to_project(json_path),
        },
        payload={
            "import_count": len(imported_rows),
            "skipped_count": len(blocked_rows),
            "imported_codes": [row["ts_code"] for row in imported_rows],
            "dry_run": False,
        },
        created_at=created_at,
    )
    conn.commit()
    conn.close()

    log_run(
        "import_live_positions.py",
        "success",
        "live positions imported",
        {
            "input_rel_path": relative_to_project(input_path),
            "import_count": len(imported_rows),
            "skipped_count": len(blocked_rows),
            "markdown_rel_path": relative_to_project(markdown_path),
            "json_rel_path": relative_to_project(json_path),
            "dry_run": False,
        },
    )
    print(f"Live position import markdown: {markdown_path}")
    print(f"Live position import json: {json_path}")
    print(f"Imported rows: {len(imported_rows)}")
    print(f"Skipped rows: {len(blocked_rows)}")


if __name__ == "__main__":
    main()
