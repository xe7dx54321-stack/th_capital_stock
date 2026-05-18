#!/usr/bin/env python3
"""Minimal SMR agent runtime helpers for profiles, routing, and handoffs."""

import json
import os
from pathlib import Path

from smr_paths import env_or_project_path, normalize_project_path, project_path, relative_to_project
from smr_registry import get_entity_snapshot, register_snapshot
from smr_wiki import generate_execution_id, now_ts

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
AGENT_ROOT = env_or_project_path("SMR_AGENT_ROOT", "12_smr_agents")
PROFILE_DIR = normalize_project_path(os.environ.get("SMR_AGENT_PROFILE_DIR")) or (AGENT_ROOT / "profiles")
HANDOFF_DIR = normalize_project_path(os.environ.get("SMR_HANDOFF_DIR")) or (AGENT_ROOT / "handoffs")
WORKSPACE_DIR = normalize_project_path(os.environ.get("SMR_AGENT_WORKSPACE_DIR")) or (AGENT_ROOT / "workspaces")

HANDOFF_STATUSES = {"pending", "accepted", "completed", "rejected", "cancelled"}
ACTIVE_HANDOFF_STATUSES = {"pending", "accepted"}

DEFAULT_REQUIRED_ACTIONS = {
    "daily_report_candidate": "review_daily_candidate",
    "daily_reporting_snapshot": "review_daily_surface",
    "dynamic_pool_snapshot": "explain_pool_changes",
    "ingest_draft_batch": "triage_ingest_drafts",
    "ingest_draft_scan": "resolve_blocked_drafts",
    "portfolio_pnl_snapshot": "review_portfolio_snapshot",
    "research_context_note": "merge_context_into_dispatch",
    "research_quality_snapshot": "review_research_quality",
    "review_queue": "review_queue_triage",
    "rotation_candidate_snapshot": "review_rotation_candidates",
    "rotation_execution_plan_snapshot": "review_rotation_execution_plan",
    "portfolio_action_memo_snapshot": "review_portfolio_action_memo",
    "risk_update_candidate": "merge_risk_into_dispatch",
    "risk_monitor_snapshot": "interpret_risk_snapshot",
    "source_manifest": "promote_manifest_to_draft",
    "stock_objective_monitor_snapshot": "review_objective_monitor",
    "strategy_watch_batch": "review_strategy_watch",
    "system_change_request": "prepare_system_patch_candidate",
    "system_patch_candidate": "review_system_patch_candidate",
    "system_validation_snapshot": "review_system_validation",
    "trend_research_batch": "review_research_batch",
    "us_signal_snapshot": "interpret_us_signal",
    "wiki_draft": "review_and_import",
    "wiki_knowledge_entry": "refresh_knowledge_entry",
}

DEFAULT_HANDOFF_TYPES = {
    "daily_report_candidate": "report_review",
    "daily_reporting_snapshot": "report_review",
    "dynamic_pool_snapshot": "research_review",
    "ingest_draft_batch": "research_review",
    "ingest_draft_scan": "research_review",
    "portfolio_pnl_snapshot": "risk_review",
    "research_context_note": "report_sync",
    "research_quality_snapshot": "research_review",
    "review_queue": "research_review",
    "rotation_candidate_snapshot": "research_review",
    "rotation_execution_plan_snapshot": "research_review",
    "portfolio_action_memo_snapshot": "research_review",
    "risk_update_candidate": "report_sync",
    "risk_monitor_snapshot": "risk_review",
    "source_manifest": "knowledge_ingest",
    "stock_objective_monitor_snapshot": "research_review",
    "strategy_watch_batch": "research_review",
    "system_change_request": "engineering_execution",
    "system_patch_candidate": "engineering_review",
    "system_validation_snapshot": "engineering_review",
    "trend_research_batch": "research_review",
    "us_signal_snapshot": "research_review",
    "wiki_draft": "knowledge_review",
    "wiki_knowledge_entry": "knowledge_refresh",
}


def ensure_agent_runtime_dirs():
    for path in (AGENT_ROOT, PROFILE_DIR, HANDOFF_DIR, WORKSPACE_DIR):
        path.mkdir(parents=True, exist_ok=True)


def ensure_agent_handoff_state_table(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS agent_handoff_state (
            handoff_id TEXT PRIMARY KEY,
            lane TEXT NOT NULL,
            status TEXT NOT NULL,
            handoff_type TEXT NOT NULL,
            from_profile_id TEXT NOT NULL,
            to_profile_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            source_entry_id TEXT,
            required_action TEXT NOT NULL,
            inputs_json TEXT NOT NULL DEFAULT '{}',
            expected_outputs_json TEXT NOT NULL DEFAULT '{}',
            outputs_json TEXT DEFAULT 'null',
            resolution_summary TEXT,
            history_json TEXT NOT NULL DEFAULT '[]',
            handoff_path TEXT,
            handoff_rel_path TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_agent_handoff_state_status_profile
        ON agent_handoff_state(status, to_profile_id, updated_at DESC);

        CREATE INDEX IF NOT EXISTS idx_agent_handoff_state_entity
        ON agent_handoff_state(entity_type, entity_id, updated_at DESC);
        """
    )


def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def _attach_handoff_paths(record):
    handoff_id = record.get("handoff_id")
    if not handoff_id:
        return record
    path = Path(record.get("handoff_path") or (HANDOFF_DIR / f"{handoff_id}.json"))
    record["handoff_path"] = str(path)
    record["handoff_rel_path"] = relative_to_project(path)
    return record


def _persist_handoff_record(record):
    record = _attach_handoff_paths(record)
    path = Path(record["handoff_path"])
    _write_json(path, {k: v for k, v in record.items() if k not in {"handoff_path", "handoff_rel_path"}})
    record["handoff_path"] = str(path)
    record["handoff_rel_path"] = relative_to_project(path)
    return record


def _parse_json_text(text, default):
    if text in (None, ""):
        return default
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return default


def upsert_handoff_state(conn, record):
    ensure_agent_handoff_state_table(conn)
    normalized = _attach_handoff_paths(dict(record))
    conn.execute(
        """
        INSERT INTO agent_handoff_state (
            handoff_id,
            lane,
            status,
            handoff_type,
            from_profile_id,
            to_profile_id,
            entity_type,
            entity_id,
            source_entry_id,
            required_action,
            inputs_json,
            expected_outputs_json,
            outputs_json,
            resolution_summary,
            history_json,
            handoff_path,
            handoff_rel_path,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(handoff_id) DO UPDATE SET
            lane=excluded.lane,
            status=excluded.status,
            handoff_type=excluded.handoff_type,
            from_profile_id=excluded.from_profile_id,
            to_profile_id=excluded.to_profile_id,
            entity_type=excluded.entity_type,
            entity_id=excluded.entity_id,
            source_entry_id=excluded.source_entry_id,
            required_action=excluded.required_action,
            inputs_json=excluded.inputs_json,
            expected_outputs_json=excluded.expected_outputs_json,
            outputs_json=excluded.outputs_json,
            resolution_summary=excluded.resolution_summary,
            history_json=excluded.history_json,
            handoff_path=excluded.handoff_path,
            handoff_rel_path=excluded.handoff_rel_path,
            created_at=excluded.created_at,
            updated_at=excluded.updated_at
        """,
        (
            normalized["handoff_id"],
            normalized["lane"],
            normalized["status"],
            normalized["handoff_type"],
            normalized["from_profile_id"],
            normalized["to_profile_id"],
            normalized["entity_type"],
            normalized["entity_id"],
            normalized.get("source_entry_id"),
            normalized["required_action"],
            json.dumps(normalized.get("inputs") or {}, ensure_ascii=False, sort_keys=True),
            json.dumps(normalized.get("expected_outputs") or {}, ensure_ascii=False, sort_keys=True),
            json.dumps(normalized.get("outputs"), ensure_ascii=False, sort_keys=True),
            normalized.get("resolution_summary"),
            json.dumps(normalized.get("history") or [], ensure_ascii=False, sort_keys=True),
            normalized.get("handoff_path"),
            normalized.get("handoff_rel_path"),
            normalized["created_at"],
            normalized["updated_at"],
        ),
    )
    return normalized


def query_handoff_state(
    conn,
    handoff_id=None,
    status=None,
    to_profile_id=None,
    from_profile_id=None,
    entity_type=None,
    entity_id=None,
    limit=20,
):
    ensure_agent_handoff_state_table(conn)
    filters = []
    params = []
    if handoff_id:
        filters.append("handoff_id=?")
        params.append(handoff_id)
    if status:
        filters.append("status=?")
        params.append(status)
    if to_profile_id:
        filters.append("to_profile_id=?")
        params.append(to_profile_id)
    if from_profile_id:
        filters.append("from_profile_id=?")
        params.append(from_profile_id)
    if entity_type:
        filters.append("entity_type=?")
        params.append(entity_type)
    if entity_id:
        filters.append("entity_id=?")
        params.append(entity_id)

    query = """
        SELECT
            handoff_id,
            lane,
            status,
            handoff_type,
            from_profile_id,
            to_profile_id,
            entity_type,
            entity_id,
            source_entry_id,
            required_action,
            inputs_json,
            expected_outputs_json,
            outputs_json,
            resolution_summary,
            history_json,
            handoff_path,
            handoff_rel_path,
            created_at,
            updated_at
        FROM agent_handoff_state
    """
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY datetime(updated_at) DESC, handoff_id DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    results = []
    for row in rows:
        record = {
            "handoff_id": row[0],
            "lane": row[1],
            "status": row[2],
            "handoff_type": row[3],
            "from_profile_id": row[4],
            "to_profile_id": row[5],
            "entity_type": row[6],
            "entity_id": row[7],
            "source_entry_id": row[8],
            "required_action": row[9],
            "inputs": _parse_json_text(row[10], {}),
            "expected_outputs": _parse_json_text(row[11], {}),
            "outputs": _parse_json_text(row[12], None),
            "resolution_summary": row[13],
            "history": _parse_json_text(row[14], []),
            "handoff_path": row[15],
            "handoff_rel_path": row[16],
            "created_at": row[17],
            "updated_at": row[18],
        }
        results.append(_attach_handoff_paths(record))
    return results


def sync_handoff_state_from_disk(conn, handoff_ids=None, limit=500, statuses=None):
    ensure_agent_runtime_dirs()
    requested_ids = {str(value).strip() for value in (handoff_ids or []) if str(value).strip()}
    allowed_statuses = {str(value).strip() for value in (statuses or []) if str(value).strip()}
    synced = 0
    for path in sorted(HANDOFF_DIR.glob("*.json"), reverse=True):
        handoff_id = path.stem
        if requested_ids and handoff_id not in requested_ids:
            continue
        record = _attach_handoff_paths(_load_json(path))
        if allowed_statuses and record.get("status") not in allowed_statuses:
            continue
        upsert_handoff_state(conn, record)
        synced += 1
        if synced >= max(limit, 0):
            break
    return synced


def list_profiles(lane=None):
    ensure_agent_runtime_dirs()
    profiles = []
    for path in sorted(PROFILE_DIR.glob("*.json")):
        profile = _load_json(path)
        profile["profile_path"] = str(path)
        profile["profile_rel_path"] = relative_to_project(path)
        if lane and profile.get("lane") != lane:
            continue
        profiles.append(profile)
    return sorted(
        profiles,
        key=lambda profile: (
            -int(profile.get("priority", 100)),
            profile.get("profile_id", ""),
        ),
    )


def get_profile(profile_id):
    for profile in list_profiles():
        if profile.get("profile_id") == profile_id:
            return profile
    raise ValueError(f"Unknown agent profile: {profile_id}")


def profile_workspace_path(profile):
    rel_path = profile.get("workspace_rel_path")
    if not rel_path:
        return WORKSPACE_DIR

    override_root = normalize_project_path(os.environ.get("SMR_AGENT_WORKSPACE_DIR"))
    if override_root is not None:
        parts = Path(rel_path).parts
        if "workspaces" in parts:
            suffix = Path(*parts[parts.index("workspaces") + 1 :])
            return (override_root / suffix).resolve(strict=False)
        return (override_root / Path(rel_path).name).resolve(strict=False)

    normalized = normalize_project_path(rel_path)
    if normalized is not None:
        return normalized
    return (WORKSPACE_DIR / Path(rel_path).name).resolve(strict=False)


def profile_match_entity_types(profile):
    return set(profile.get("match", {}).get("entity_types", []))


def get_registry_entry_by_id(conn, entry_id):
    row = conn.execute(
        """
        SELECT
            id,
            entity_type,
            entity_id,
            status,
            source,
            relationships_json,
            payload_json,
            snapshot_index,
            created_at
        FROM task_registry_entry
        WHERE id=?
        LIMIT 1
        """,
        (entry_id,),
    ).fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "entity_type": row[1],
        "entity_id": row[2],
        "status": row[3],
        "source": row[4],
        "relationships": json.loads(row[5] or "{}"),
        "payload": json.loads(row[6] or "{}"),
        "snapshot_index": row[7],
        "created_at": row[8],
    }


def get_latest_registry_entry(conn, entity_type, entity_id):
    snapshot = get_entity_snapshot(conn, entity_type, entity_id, limit=1)
    if not snapshot:
        return None
    return snapshot["latest_entry"]


def default_required_action(entry, to_profile_id):
    if to_profile_id == "openclaw_system_exec":
        return DEFAULT_REQUIRED_ACTIONS.get(entry["entity_type"], "prepare_system_patch_candidate")
    if to_profile_id == "hermes_risk_curator":
        return DEFAULT_REQUIRED_ACTIONS.get(entry["entity_type"], "review_risk_context")
    if to_profile_id == "hermes_reporting_editor":
        return DEFAULT_REQUIRED_ACTIONS.get(entry["entity_type"], "review_reporting_context")
    return DEFAULT_REQUIRED_ACTIONS.get(entry["entity_type"], "review_subject")


def default_handoff_type(entry, to_profile_id):
    if to_profile_id == "openclaw_system_exec":
        return DEFAULT_HANDOFF_TYPES.get(entry["entity_type"], "engineering_execution")
    if to_profile_id == "hermes_risk_curator":
        return DEFAULT_HANDOFF_TYPES.get(entry["entity_type"], "risk_review")
    if to_profile_id == "hermes_reporting_editor":
        return DEFAULT_HANDOFF_TYPES.get(entry["entity_type"], "report_review")
    return DEFAULT_HANDOFF_TYPES.get(entry["entity_type"], "knowledge_review")


def default_expected_outputs(entry, to_profile_id):
    if to_profile_id == "openclaw_system_exec":
        return {
            "task_spec": True,
            "patch_candidate": True,
            "validation_plan": True,
            "verification_summary": True,
            "commit_candidate": True,
        }
    if to_profile_id == "hermes_risk_curator":
        return {
            "risk_explanation": True,
            "reason_code": True,
            "playbook_candidate": True,
        }
    if to_profile_id == "hermes_reporting_editor":
        return {
            "daily_note": True,
            "dispatch_update": True,
            "knowledge_candidate": True,
        }
    return {
        "structured_summary": True,
        "reason_code": True,
        "knowledge_candidate": True,
    }


def should_suggest_handoff(entry):
    entity_type = entry["entity_type"]
    payload = entry.get("payload", {})

    if entity_type == "system_change_request":
        return (payload.get("request_count") or 0) > 0
    if entity_type == "system_patch_candidate":
        return bool(payload.get("patch_candidate_rel_path") or payload.get("task_spec_rel_path"))
    if entity_type == "system_validation_snapshot":
        return bool(payload.get("validation_plan_rel_path") or payload.get("verification_summary_rel_path"))
    if entity_type == "review_queue":
        return (payload.get("item_count") or 0) > 0
    if entity_type == "dynamic_pool_snapshot":
        active_codes = payload.get("active_codes_by_pool") or {}
        return (
            (payload.get("structured_decisions") or 0) > 0
            or bool(active_codes.get("recommended"))
            or bool(active_codes.get("candidate"))
        )
    if entity_type == "stock_objective_monitor_snapshot":
        return (payload.get("focus_count") or 0) > 0
    if entity_type == "strategy_watch_batch":
        return (payload.get("item_count") or 0) > 0
    if entity_type == "trend_research_batch":
        return (payload.get("target_count") or 0) > 0
    if entity_type == "research_context_note":
        return bool(payload.get("note_rel_path"))
    if entity_type == "research_quality_snapshot":
        return (payload.get("row_count") or 0) > 0
    if entity_type == "rotation_candidate_snapshot":
        return (payload.get("opportunity_count") or 0) > 0 or (payload.get("rotation_pair_count") or 0) > 0
    if entity_type == "rotation_execution_plan_snapshot":
        return (payload.get("plan_count") or 0) > 0
    if entity_type == "portfolio_action_memo_snapshot":
        return (payload.get("action_count") or 0) > 0
    if entity_type == "portfolio_pnl_snapshot":
        return (payload.get("open_position_count") or 0) > 0 and (
            (payload.get("losing_positions") or 0) > 0
            or (payload.get("total_pnl") or 0) < 0
        )
    if entity_type == "daily_report_candidate":
        return bool(payload.get("candidate_rel_path")) or bool(payload.get("candidate_summary"))
    if entity_type == "risk_update_candidate":
        return bool(payload.get("risk_candidate_rel_path"))
    if entity_type == "risk_monitor_snapshot":
        return (payload.get("alert_count") or 0) > 0
    if entity_type == "us_signal_snapshot":
        return entry.get("status") not in {"no_change", None, ""} and (payload.get("saved_count") or 0) > 0
    if entity_type == "daily_reporting_snapshot":
        return bool(payload.get("latest_report_rel_path"))
    return True


def suggested_handoff(entry, profile):
    target_profile_id = profile.get("suggested_handoffs", {}).get(entry["entity_type"])
    if not target_profile_id:
        return None
    if not should_suggest_handoff(entry):
        return None
    return {
        "to_profile_id": target_profile_id,
        "required_action": default_required_action(entry, target_profile_id),
        "handoff_type": default_handoff_type(entry, target_profile_id),
        "expected_outputs": default_expected_outputs(entry, target_profile_id),
    }


def route_entry(entry):
    for profile in list_profiles():
        if entry["entity_type"] not in profile_match_entity_types(profile):
            continue
        handoff = suggested_handoff(entry, profile)
        return {
            "matched": True,
            "entry": entry,
            "profile_id": profile["profile_id"],
            "lane": profile["lane"],
            "role": profile.get("role"),
            "workspace_rel_path": profile.get("workspace_rel_path"),
            "match_reason": f"entity_type={entry['entity_type']}",
            "suggested_handoff": handoff,
        }
    return {
        "matched": False,
        "entry": entry,
        "profile_id": None,
        "lane": None,
        "role": None,
        "workspace_rel_path": None,
        "match_reason": "no matching profile",
        "suggested_handoff": None,
    }


def list_handoffs(status=None, to_profile_id=None, from_profile_id=None, limit=20):
    ensure_agent_runtime_dirs()
    results = []
    for path in sorted(HANDOFF_DIR.glob("*.json"), reverse=True):
        record = _attach_handoff_paths(_load_json(path))
        if status and record.get("status") != status:
            continue
        if to_profile_id and record.get("to_profile_id") != to_profile_id:
            continue
        if from_profile_id and record.get("from_profile_id") != from_profile_id:
            continue
        results.append(record)
        if len(results) >= limit:
            break
    return results


def get_handoff(handoff_id):
    path = HANDOFF_DIR / f"{handoff_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Unknown handoff: {handoff_id}")
    return _attach_handoff_paths(_load_json(path))


def merged_inputs_from_entry(existing_inputs, entry):
    inputs = dict(existing_inputs or {})
    registry_entry_ids = [entry["id"]]
    for value in inputs.get("registry_entry_ids") or []:
        if value in (None, "", entry["id"]):
            continue
        registry_entry_ids.append(value)
    inputs.update(
        {
            "registry_entry_ids": registry_entry_ids,
            "entity_status": entry["status"],
            "source": entry["source"],
            "snapshot_index": entry["snapshot_index"],
            "relationships": entry.get("relationships", {}),
        }
    )
    return inputs


def default_inputs_from_entry(entry):
    return merged_inputs_from_entry({}, entry)


def effective_handoff_source_entry(conn, handoff, prefer_latest=True):
    bound_entry = None
    source_entry_id = handoff.get("source_entry_id")
    if source_entry_id:
        bound_entry = get_registry_entry_by_id(conn, source_entry_id)

    latest_entry = get_latest_registry_entry(conn, handoff["entity_type"], handoff["entity_id"])
    if prefer_latest and latest_entry is not None:
        return latest_entry
    if bound_entry is not None:
        return bound_entry
    if latest_entry is not None:
        return latest_entry
    return None


def sync_handoff_source_entry(
    conn,
    handoff,
    entry,
    updated_by="sync_handoff_source_entry",
    note=None,
):
    if not entry or handoff.get("status") not in ACTIVE_HANDOFF_STATUSES:
        return handoff, False

    new_inputs = merged_inputs_from_entry(handoff.get("inputs"), entry)
    if handoff.get("source_entry_id") == entry["id"] and handoff.get("inputs") == new_inputs:
        return handoff, False

    updated_at = now_ts()
    record = dict(handoff)
    record["source_entry_id"] = entry["id"]
    record["inputs"] = new_inputs
    record["updated_at"] = updated_at
    record.setdefault("history", []).append(
        {
            "status": record["status"],
            "at": updated_at,
            "by": updated_by,
            "note": note or f"handoff source entry refreshed to {entry['id']}",
        }
    )

    record = _persist_handoff_record(record)
    upsert_handoff_state(conn, record)

    register_snapshot(
        conn,
        entity_type="agent_handoff",
        entity_id=record["handoff_id"],
        status=record["status"],
        source=updated_by,
        relationships={
            "from_profile_id": record["from_profile_id"],
            "to_profile_id": record["to_profile_id"],
            "entity_type": record["entity_type"],
            "entity_id": record["entity_id"],
        },
        payload=_handoff_registry_payload(record),
    )
    return record, True


def load_handoff_source_entry(
    conn,
    handoff,
    prefer_latest=True,
    sync_active=False,
    updated_by="load_handoff_source_entry",
    note=None,
):
    entry = effective_handoff_source_entry(conn, handoff, prefer_latest=prefer_latest)
    if entry is None:
        return handoff, None, False
    record = handoff
    refreshed = False
    if sync_active:
        record, refreshed = sync_handoff_source_entry(
            conn,
            handoff,
            entry,
            updated_by=updated_by,
            note=note,
        )
    return record, entry, refreshed


def _handoff_lane(from_profile_id, to_profile_id):
    from_profile = get_profile(from_profile_id)
    to_profile = get_profile(to_profile_id)
    return f"{from_profile['lane']}_to_{to_profile['lane']}"


def _handoff_registry_payload(record):
    return {
        "handoff_type": record["handoff_type"],
        "from_profile_id": record["from_profile_id"],
        "to_profile_id": record["to_profile_id"],
        "entity_type": record["entity_type"],
        "entity_id": record["entity_id"],
        "required_action": record["required_action"],
        "source_entry_id": record.get("source_entry_id"),
        "handoff_rel_path": record["handoff_rel_path"],
        "updated_at": record["updated_at"],
    }


def find_active_handoff(
    entity_type,
    entity_id,
    from_profile_id,
    to_profile_id,
    required_action,
):
    for record in list_handoffs(limit=500):
        if record.get("status") not in ACTIVE_HANDOFF_STATUSES:
            continue
        if record.get("entity_type") != entity_type:
            continue
        if record.get("entity_id") != entity_id:
            continue
        if record.get("from_profile_id") != from_profile_id:
            continue
        if record.get("to_profile_id") != to_profile_id:
            continue
        if record.get("required_action") != required_action:
            continue
        return record
    return None


def ensure_auto_handoff(
    conn,
    entry,
    note=None,
    created_by="auto_handoff",
):
    route = route_entry(entry)
    suggestion = route.get("suggested_handoff")
    if not route.get("matched"):
        return {"created": False, "reason": "no_matching_profile", "route": route, "handoff": None}
    if not suggestion:
        return {"created": False, "reason": "no_suggested_handoff", "route": route, "handoff": None}

    existing = find_active_handoff(
        entity_type=entry["entity_type"],
        entity_id=entry["entity_id"],
        from_profile_id=route["profile_id"],
        to_profile_id=suggestion["to_profile_id"],
        required_action=suggestion["required_action"],
    )
    if existing:
        existing, refreshed = sync_handoff_source_entry(
            conn,
            existing,
            entry,
            updated_by=created_by,
            note=note or f"active handoff rebound to latest source entry {entry['id']}",
        )
        return {
            "created": False,
            "reason": "refreshed_existing_active_handoff" if refreshed else "existing_active_handoff",
            "route": route,
            "handoff": existing,
        }

    record = create_handoff(
        conn,
        from_profile_id=route["profile_id"],
        to_profile_id=suggestion["to_profile_id"],
        handoff_type=suggestion["handoff_type"],
        entity_type=entry["entity_type"],
        entity_id=entry["entity_id"],
        required_action=suggestion["required_action"],
        source_entry_id=entry["id"],
        inputs=default_inputs_from_entry(entry),
        expected_outputs=suggestion["expected_outputs"],
        note=note,
        created_by=created_by,
    )
    return {"created": True, "reason": "created", "route": route, "handoff": record}


def create_handoff(
    conn,
    from_profile_id,
    to_profile_id,
    handoff_type,
    entity_type,
    entity_id,
    required_action,
    source_entry_id=None,
    inputs=None,
    expected_outputs=None,
    note=None,
    created_by="create_handoff.py",
):
    ensure_agent_runtime_dirs()
    handoff_id = generate_execution_id("handoff")
    created_at = now_ts()
    record = {
        "handoff_id": handoff_id,
        "lane": _handoff_lane(from_profile_id, to_profile_id),
        "status": "pending",
        "handoff_type": handoff_type,
        "from_profile_id": from_profile_id,
        "to_profile_id": to_profile_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "source_entry_id": source_entry_id,
        "required_action": required_action,
        "inputs": inputs or {},
        "expected_outputs": expected_outputs or {},
        "history": [
            {
                "status": "pending",
                "at": created_at,
                "by": created_by,
                "note": note or "handoff created",
            }
        ],
        "created_at": created_at,
        "updated_at": created_at,
    }

    path = HANDOFF_DIR / f"{handoff_id}.json"
    record["handoff_path"] = str(path)
    record["handoff_rel_path"] = relative_to_project(path)
    record = _persist_handoff_record(record)
    upsert_handoff_state(conn, record)

    register_snapshot(
        conn,
        entity_type="agent_handoff",
        entity_id=handoff_id,
        status="pending",
        source=created_by,
        relationships={
            "from_profile_id": from_profile_id,
            "to_profile_id": to_profile_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
        },
        payload=_handoff_registry_payload(record),
    )
    return record


def resolve_handoff(
    conn,
    handoff_id,
    status,
    resolved_by,
    summary=None,
    outputs=None,
    source="resolve_handoff.py",
):
    if status not in HANDOFF_STATUSES:
        raise ValueError(f"Unsupported handoff status: {status}")

    record = get_handoff(handoff_id)
    updated_at = now_ts()
    record["status"] = status
    record["updated_at"] = updated_at
    if summary:
        record["resolution_summary"] = summary
    if outputs is not None:
        record["outputs"] = outputs
    record.setdefault("history", []).append(
        {
            "status": status,
            "at": updated_at,
            "by": resolved_by,
            "note": summary or f"handoff marked {status}",
        }
    )

    record = _persist_handoff_record(record)
    upsert_handoff_state(conn, record)

    register_snapshot(
        conn,
        entity_type="agent_handoff",
        entity_id=handoff_id,
        status=status,
        source=source,
        relationships={
            "from_profile_id": record["from_profile_id"],
            "to_profile_id": record["to_profile_id"],
            "entity_type": record["entity_type"],
            "entity_id": record["entity_id"],
        },
        payload=_handoff_registry_payload(record),
    )
    return record


def requeue_handoff(
    conn,
    handoff_id,
    requeued_by,
    summary=None,
    source="requeue_handoff.py",
    prefer_latest=True,
):
    record = get_handoff(handoff_id)
    entry = effective_handoff_source_entry(conn, record, prefer_latest=prefer_latest)
    if entry is not None:
        record["source_entry_id"] = entry["id"]
        record["inputs"] = merged_inputs_from_entry(record.get("inputs"), entry)

    updated_at = now_ts()
    record["status"] = "pending"
    record["updated_at"] = updated_at
    record.pop("resolution_summary", None)
    record.pop("outputs", None)
    record.setdefault("history", []).append(
        {
            "status": "pending",
            "at": updated_at,
            "by": requeued_by,
            "note": summary or "handoff requeued",
        }
    )

    record = _persist_handoff_record(record)
    upsert_handoff_state(conn, record)
    register_snapshot(
        conn,
        entity_type="agent_handoff",
        entity_id=handoff_id,
        status="pending",
        source=source,
        relationships={
            "from_profile_id": record["from_profile_id"],
            "to_profile_id": record["to_profile_id"],
            "entity_type": record["entity_type"],
            "entity_id": record["entity_id"],
        },
        payload=_handoff_registry_payload(record),
    )
    return record
