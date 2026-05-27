#!/usr/bin/env python3
"""Safe dry-run command generation for Phase 32 evidence review workbench."""

from __future__ import annotations

from typing import Any

from smr_sensitive_variable_guard import FORBIDDEN_CONFIRMED_UPGRADES, is_sensitive_variable


SAFE_REVIEW_ACTIONS = {
    "approve_evidence",
    "reject_evidence",
    "downgrade_usage",
    "mark_as_noise",
    "request_better_source",
    "link_to_variable_pack",
    "archive_evidence",
}

DEFAULT_TARGET_USAGE = "context_only"
ACTION_SCRIPT = "08_scripts/jobs/apply_evidence_review_action.py"
REPAIR_SCRIPT = "08_scripts/jobs/upsert_download_unavailable_repair_tasks.py"
BATCH_DRY_RUN_SCRIPT = "08_scripts/jobs/run_phase32_batch_review_dry_run.py"


def _compact(value: Any) -> str:
    return " ".join(str(value or "").split())


def _shell_arg(value: Any) -> str:
    text = str(value or "")
    escaped = text.replace('"', '\\"')
    if not escaped or any(ch.isspace() for ch in escaped) or any(ch in escaped for ch in ['"', "'", ";", "&", "|"]):
        return f'"{escaped}"'
    return escaped


def _has_noise(item: dict[str, Any]) -> bool:
    return bool(item.get("noise_flags")) or item.get("lifecycle_status") == "marked_noise"


def recommended_action_for_item(item: dict[str, Any]) -> str:
    """Choose a conservative dry-run action recommendation for a workbench item."""

    if item.get("item_type") == "download_repair":
        return "request_better_source"
    if item.get("source_url_missing"):
        return "request_better_source"
    lifecycle_status = str(item.get("lifecycle_status") or "")
    review_status = str(item.get("review_status") or "")
    quality_bucket = str(item.get("quality_bucket") or "")
    if lifecycle_status in {"rejected_evidence", "removed", "archived"}:
        return "archive_evidence"
    if _has_noise(item):
        return "mark_as_noise"
    if is_sensitive_variable(item.get("variable_type")):
        return "downgrade_usage"
    if review_status == "review_required" or quality_bucket in {"weak_but_usable", "review_required"}:
        return "downgrade_usage"
    if item.get("linked_variable_pack") and item.get("link_status") == "requires_review":
        return "downgrade_usage"
    return "approve_evidence"


def action_parameters_for_item(item: dict[str, Any], action: str | None = None) -> dict[str, Any]:
    selected = action or item.get("recommended_action") or recommended_action_for_item(item)
    if selected not in SAFE_REVIEW_ACTIONS:
        selected = recommended_action_for_item(item)
    params: dict[str, Any] = {"action": selected, "target_usage": None, "reason": None}
    if selected == "downgrade_usage":
        params["target_usage"] = DEFAULT_TARGET_USAGE
        params["reason"] = "phase32 review: conservative usage downgrade dry-run"
    elif selected == "reject_evidence":
        params["reason"] = "phase32 review: quoted span requires rejection reason"
    elif selected == "mark_as_noise":
        params["reason"] = "phase32 review: noisy or insufficient evidence"
    elif selected == "request_better_source":
        params["reason"] = "phase32 review: better source requested"
    elif selected == "archive_evidence":
        params["reason"] = "phase32 review: archive after governance review"
    elif selected == "link_to_variable_pack":
        params["reason"] = "phase32 review: link dry-run still requires variable pack gate"
    return params


def build_dry_run_command(item: dict[str, Any], *, action: str | None = None) -> dict[str, Any]:
    evidence_id = item.get("evidence_id")
    selected_action = action or item.get("recommended_action") or recommended_action_for_item(item)
    if selected_action not in SAFE_REVIEW_ACTIONS:
        selected_action = recommended_action_for_item(item)
    if is_sensitive_variable(item.get("variable_type")) and selected_action == "approve_evidence":
        selected_action = "downgrade_usage"
    params = action_parameters_for_item(item, selected_action)
    blocked_reason = None
    command = None
    if not evidence_id and item.get("item_type") == "download_repair":
        command = f"python {REPAIR_SCRIPT} --dry-run --json"
        selected_action = "request_better_source"
    elif evidence_id and item.get("persisted_in_evidence_store") is False:
        command = f"python {BATCH_DRY_RUN_SCRIPT} --evidence-id {_shell_arg(evidence_id)} --dry-run --json"
    elif not evidence_id:
        blocked_reason = "review action command requires evidence_id; use the download repair workbench for source repair tasks"
    elif selected_action in FORBIDDEN_CONFIRMED_UPGRADES:
        blocked_reason = f"forbidden action blocked: {selected_action}"
    else:
        parts = [
            "python",
            ACTION_SCRIPT,
            "--evidence-id",
            _shell_arg(evidence_id),
            "--action",
            _shell_arg(selected_action),
        ]
        if params.get("target_usage"):
            parts.extend(["--target-usage", _shell_arg(params["target_usage"])])
        if params.get("reason"):
            parts.extend(["--reason", _shell_arg(params["reason"])])
        parts.extend(["--dry-run", "--json"])
        command = " ".join(parts)
    return {
        "evidence_id": evidence_id,
        "recommended_action": selected_action,
        "dry_run_command": command,
        "execute_command_available": False,
        "blocked_reason": blocked_reason,
        "action_parameters": params,
        "safety_notes": [
            "dry-run only by default",
            "does not allow promotion",
            "does not confirm sensitive variables",
            "does not create pending review",
            "does not create paper orders",
        ],
    }


def attach_action_command(item: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(item)
    if enriched.get("recommended_action") not in SAFE_REVIEW_ACTIONS:
        enriched["recommended_action"] = recommended_action_for_item(enriched)
    command = build_dry_run_command(enriched)
    enriched["action_command"] = command
    enriched["action_command_dry_run"] = command.get("dry_run_command")
    enriched["execute_command_available"] = False
    return enriched
