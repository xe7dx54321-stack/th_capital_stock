#!/usr/bin/env python3
"""Report current and projected SMR model-shadow readiness by routed entity type."""

import argparse
import os
import sys
from copy import deepcopy
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_llm import load_model_profiles, load_task_routes, provider_readiness, resolve_model_route, shadow_execution_status
from smr_paths import normalize_project_path

FIRST_WAVE_PRIORITIES = {
    "risk_monitor_snapshot": ("P1-first", "风险链最适合第一批真实 shadow"),
    "us_signal_snapshot": ("P1-first", "显著美股信号链短、清晰、易观察"),
    "daily_reporting_snapshot": ("P1-first", "日报增强链价值高且只写候选层"),
    "dynamic_pool_snapshot": ("P1-second", "适合在第一批稳定后进入"),
    "research_quality_snapshot": ("P1-second", "适合做研究缺口归纳增强"),
    "portfolio_pnl_snapshot": ("P1-second", "适合补组合风险解释，但需控制措辞"),
    "research_context_note": ("P1-second", "适合做 dispatch 同步增强"),
    "risk_update_candidate": ("P1-second", "适合做风险同步增强"),
    "trend_research_batch": ("P1-second", "已切到 MiniMax 长上下文槽位，适合在首批稳定后进入"),
    "review_queue": ("P2-later", "治理分诊价值高，但不适合作为第一批真实 shadow"),
    "wiki_draft": ("P2-later", "需要更强人工审核边界，不适合作为第一批"),
}


def prompt_pack_exists(route):
    rel_path = route.get("prompt_pack_rel_path")
    path = normalize_project_path(rel_path)
    return bool(path and path.exists())


def projected_shadow_route(route):
    projected = deepcopy(route)
    projected["global_mode"] = "shadow"
    projected["route_global_mode"] = "shadow"

    readiness = dict(projected.get("provider_readiness") or {})
    readiness["enabled"] = True
    readiness["has_api_key"] = bool(readiness.get("has_api_key"))
    readiness["has_base_url"] = bool(readiness.get("has_base_url"))
    projected["provider_readiness"] = readiness
    return projected


def summarize_entity(entity_type, route_config):
    route = resolve_model_route(entity_type, route_config.get("to_profile_id"))
    projected_route = projected_shadow_route(route)
    current_gate = shadow_execution_status(route)
    projected_gate = shadow_execution_status(projected_route)
    priority, note = FIRST_WAVE_PRIORITIES.get(entity_type, ("P2-later", "未进入当前首批建议名单"))
    return {
        "entity_type": entity_type,
        "to_profile_id": route_config.get("to_profile_id") or "",
        "provider": route.get("provider") or "",
        "model": route.get("model") or "",
        "task_kind": route.get("task_kind") or "",
        "prompt_pack_ok": prompt_pack_exists(route),
        "current_gate": current_gate,
        "projected_gate": projected_gate,
        "priority": priority,
        "note": note,
    }


def sort_key(item):
    priority_order = {"P1-first": 0, "P1-second": 1, "P1-blocked": 2, "P2-later": 3}
    return (priority_order.get(item["priority"], 9), item["entity_type"])


def print_summary(rows):
    profiles = load_model_profiles()
    openai = provider_readiness("openai", profiles)
    minimax = provider_readiness("minimax", profiles)
    anthropic = provider_readiness("anthropic", profiles)
    print("SMR model shadow readiness report")
    print(f"- current_global_mode: {profiles.get('global_mode')}")
    print(f"- openai_enabled: {bool(openai.get('enabled'))}")
    print(f"- openai_api_key_available: {bool(openai.get('has_api_key'))}")
    print(f"- openai_base_url_available: {bool(openai.get('has_base_url'))}")
    print(f"- openai_fallback_source: {openai.get('fallback_source') or ''}")
    print(f"- minimax_enabled: {bool(minimax.get('enabled'))}")
    print(f"- minimax_api_key_available: {bool(minimax.get('has_api_key'))}")
    print(f"- minimax_api_key_env: {minimax.get('resolved_api_key_env') or minimax.get('api_key_env') or ''}")
    print(f"- minimax_base_url_available: {bool(minimax.get('has_base_url'))}")
    print(f"- anthropic_enabled: {bool(anthropic.get('enabled'))}")
    print(f"- anthropic_api_key_available: {bool(anthropic.get('has_api_key'))}")
    print(f"- anthropic_api_key_env: {anthropic.get('resolved_api_key_env') or anthropic.get('api_key_env') or ''}")
    print(f"- anthropic_base_url_available: {bool(anthropic.get('has_base_url'))}")
    print("- current_gate: 当前真实配置下的门禁结果")
    print("- projected_gate: 假设切到 shadow 且打开 provider 后的门禁结果")
    print("")

    for row in rows:
        print(
            f"- {row['entity_type']} -> {row['to_profile_id']} | "
            f"{row['provider']}/{row['model']} | {row['priority']}"
        )
        print(f"  task_kind={row['task_kind']}")
        print(f"  prompt_pack_ok={row['prompt_pack_ok']}")
        print(f"  current_gate={row['current_gate']}")
        print(f"  projected_gate={row['projected_gate']}")
        print(f"  note={row['note']}")


def main():
    parser = argparse.ArgumentParser(description="Report SMR model shadow readiness")
    parser.add_argument("--entity-type", action="append", help="Only inspect specific entity types")
    args = parser.parse_args()

    routes = (load_task_routes().get("entity_routes") or {})
    entity_types = args.entity_type or list(routes.keys())
    rows = []
    for entity_type in entity_types:
        route_config = routes.get(entity_type)
        if not route_config:
            rows.append(
                {
                    "entity_type": entity_type,
                    "to_profile_id": "",
                    "provider": "",
                    "model": "",
                    "task_kind": "",
                    "prompt_pack_ok": False,
                    "current_gate": "missing_route",
                    "projected_gate": "missing_route",
                    "priority": "P2-later",
                    "note": "当前没有配置路由",
                }
            )
            continue
        rows.append(summarize_entity(entity_type, route_config))

    print_summary(sorted(rows, key=sort_key))


if __name__ == "__main__":
    main()
