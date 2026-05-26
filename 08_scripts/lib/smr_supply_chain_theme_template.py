#!/usr/bin/env python3
"""Phase 25 supply-chain theme template helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from smr_paths import project_path


TEMPLATE_PATH = project_path("00_control", "supply_chain_theme_templates.json")
REQUIRED_TEMPLATE_FIELDS = {
    "description",
    "end_demand_drivers",
    "product_layers",
    "supplier_variables",
    "expectation_variables",
    "core_evidence_requirements",
}


def load_supply_chain_theme_templates(path: str | None = None) -> dict[str, Any]:
    template_path = Path(path) if path else TEMPLATE_PATH
    return json.loads(template_path.read_text(encoding="utf-8"))


def get_supply_chain_template(theme_id: str, *, templates: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = templates if templates is not None else load_supply_chain_theme_templates()
    theme = str(theme_id or "").strip()
    template = (payload.get("templates") or {}).get(theme)
    if not template:
        return {"theme_id": theme, "status": "missing", "missing_reason": "template_not_found"}
    return {"theme_id": theme, "status": "available", **template}


def validate_supply_chain_template(template: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if template.get("status") == "missing":
        return [{"severity": "error", "path": "theme_id", "message": "template missing"}]
    for field in sorted(REQUIRED_TEMPLATE_FIELDS):
        value = template.get(field)
        if not value:
            issues.append({"severity": "error", "path": field, "message": f"missing {field}"})
        elif isinstance(value, list) and not all(str(item).strip() for item in value):
            issues.append({"severity": "warning", "path": field, "message": f"{field} contains blank entries"})
    planned_sources = template.get("planned_sources") or []
    if planned_sources and not isinstance(planned_sources, list):
        issues.append({"severity": "warning", "path": "planned_sources", "message": "planned_sources should be a list"})
    return issues
