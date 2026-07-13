from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .contracts import AdapterResult, loads_json, relation_exists


@dataclass(frozen=True)
class AgentRunRequest:
    entity_id: str | None = None
    limit: int = 20


def load_agent_runs(conn: sqlite3.Connection, request: AgentRunRequest) -> AdapterResult:
    if not relation_exists(conn, "agent_runs"):
        return AdapterResult("missing", {"count": 0, "items": []})
    where = ""
    params: list[object] = []
    if request.entity_id:
        where = "WHERE UPPER(COALESCE(entity_id, ''))=?"
        params.append(request.entity_id.strip().upper())
    params.append(max(1, min(int(request.limit), 200)))
    rows = conn.execute(
        f"""
        SELECT run_id, agent_or_script, entity_type, entity_id, status, started_at,
               completed_at, output_status, block_reasons_json, metadata_json, created_at
        FROM agent_runs {where}
        ORDER BY datetime(created_at) DESC LIMIT ?
        """,
        tuple(params),
    ).fetchall()
    items = [
        {
            "run_id": row[0],
            "agent_or_script": row[1],
            "entity_type": row[2],
            "entity_id": row[3],
            "status": row[4],
            "started_at": row[5],
            "completed_at": row[6],
            "output_status": row[7],
            "block_reasons": loads_json(row[8], []),
            "metadata": loads_json(row[9], {}),
            "created_at": row[10],
        }
        for row in rows
    ]
    return AdapterResult("ok" if items else "missing", {"count": len(items), "items": items})
