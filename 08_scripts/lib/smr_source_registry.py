#!/usr/bin/env python3
"""Source registry enforcement helpers for SMR evidence pipelines."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from smr_paths import project_path

SOURCE_REGISTRY_PATH = project_path("00_control", "source_registry.md")
UNUSABLE_STATUSES = {"planned", "disabled", "deprecated", "error"}
DEGRADED_STATUSES = {"degraded"}
ACTIVE_STATUS_ALIASES = {"live": "active", "active": "active"}


def _split_markdown_row(line: str) -> list[str]:
    text = line.strip()
    if not text.startswith("|") or not text.endswith("|"):
        return []
    return [cell.strip() for cell in text.strip("|").split("|")]


def normalize_source_status(status: str | None, enabled: str | None = None) -> str:
    raw_status = str(status or "unknown").strip().lower()
    raw_enabled = str(enabled or "").strip().lower()
    if raw_enabled in {"no", "false", "0", "disabled"}:
        return "disabled"
    return ACTIVE_STATUS_ALIASES.get(raw_status, raw_status or "unknown")


def load_source_registry(path: Path | None = None) -> dict[str, dict[str, Any]]:
    path = path or SOURCE_REGISTRY_PATH
    if not path.exists():
        return {}
    lines = path.read_text(encoding="utf-8").splitlines()
    header: list[str] | None = None
    rows: dict[str, dict[str, Any]] = {}
    for line in lines:
        cells = _split_markdown_row(line)
        if not cells:
            continue
        if cells[0] == "Source Key":
            header = cells
            continue
        if header is None or cells[0].startswith("---"):
            continue
        if len(cells) < len(header):
            continue
        item = {header[index]: cells[index] for index in range(len(header))}
        source_key = item.get("Source Key")
        if not source_key:
            continue
        status = normalize_source_status(item.get("Status"), item.get("Enabled"))
        rows[source_key] = {
            "source_key": source_key,
            "source_name": item.get("Name"),
            "data_type": item.get("Layer"),
            "provider": item.get("Provider"),
            "source_class": item.get("Source Class"),
            "entity_scope": item.get("Entity Scope"),
            "markets": [part.strip() for part in re.split(r"[,/]", item.get("Markets") or "") if part.strip()],
            "update_frequency": item.get("Cadence"),
            "freshness_sla_hours": item.get("Freshness SLA Hours"),
            "status": status,
            "enabled": str(item.get("Enabled") or "").strip().lower() in {"yes", "true", "1"},
            "cost": item.get("Cost"),
            "source_quality": item.get("Confidence"),
            "owner_profile": item.get("Owner Profile"),
            "notes": item.get("Notes"),
        }
    return rows


def source_status(source_key: str | None, registry: dict[str, dict[str, Any]] | None = None) -> str:
    if not source_key:
        return "unknown"
    registry = registry if registry is not None else load_source_registry()
    item = registry.get(str(source_key))
    if not item:
        return "unknown"
    return str(item.get("status") or "unknown")


def source_is_usable(source_key: str | None, registry: dict[str, dict[str, Any]] | None = None) -> bool:
    return source_status(source_key, registry) not in UNUSABLE_STATUSES


def source_strength_multiplier(source_key: str | None, registry: dict[str, dict[str, Any]] | None = None) -> float:
    status = source_status(source_key, registry)
    if status in UNUSABLE_STATUSES:
        return 0.0
    if status in DEGRADED_STATUSES:
        return 0.5
    return 1.0


def source_registry_snapshot(registry: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    registry = registry if registry is not None else load_source_registry()
    counts: dict[str, int] = {}
    disabled_or_planned = []
    for item in registry.values():
        status = str(item.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
        if status in UNUSABLE_STATUSES:
            disabled_or_planned.append(
                {
                    "source_key": item.get("source_key"),
                    "data_type": item.get("data_type"),
                    "status": status,
                    "enabled": item.get("enabled"),
                    "impact": "只能作为 missing_data/roadmap 展示，不能作为有效 evidence。",
                }
            )
    return {
        "source_count": len(registry),
        "status_counts": counts,
        "disabled_or_planned": disabled_or_planned,
    }


def missing_data_for_source(source_key: str, impact: str | None = None) -> dict[str, Any]:
    registry = load_source_registry()
    item = registry.get(source_key) or {"source_key": source_key, "status": "unknown"}
    return {
        "source_key": source_key,
        "data_type": item.get("data_type") or source_key,
        "status": item.get("status") or "unknown",
        "impact": impact or "该来源当前不可作为有效证据，下游只能把它作为缺失能力披露。",
    }


def dumps_snapshot(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
