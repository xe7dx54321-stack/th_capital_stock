#!/usr/bin/env python3
"""Compile and optionally execute a shadow model task without touching truth layers."""

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH, get_handoff, get_latest_registry_entry, get_profile, profile_workspace_path
from smr_llm import (
    call_anthropic_messages_api,
    call_minimax_chat_completions_api,
    call_openai_responses_api,
    load_packet,
    load_prompt_pack,
    resolve_model_route,
    shadow_execution_status,
)
from smr_paths import relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

ROUTE_AUDIT_FIELDS = [
    "route_status",
    "global_mode",
    "route_global_mode",
    "task_kind",
    "model_slot",
    "packet_mode",
    "output_contract",
    "prompt_pack_rel_path",
    "provider",
    "model",
    "reasoning_effort",
]
READINESS_AUDIT_FIELDS = [
    "enabled",
    "api_key_env",
    "has_api_key",
    "base_url_env",
    "has_base_url",
    "api_style",
]
OUTPUT_PREVIEW_LIMIT = 800


def load_packet_from_handoff(conn, handoff_id):
    entry = get_latest_registry_entry(conn, "model_task_packet", handoff_id)
    if entry is None:
        raise SystemExit(f"model_task_packet not found for handoff_id: {handoff_id}")
    payload = entry.get("payload", {})
    packet_rel_path = payload.get("packet_json_rel_path")
    if not packet_rel_path:
        raise SystemExit("model_task_packet payload missing packet_json_rel_path")
    return load_packet(packet_rel_path), packet_rel_path


def safe_metadata_value(value, max_length=512):
    text = "" if value is None else str(value)
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def truncate_text(text, limit=OUTPUT_PREVIEW_LIMIT):
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def resolve_runtime_route(packet):
    packet_route = packet.get("model_route") or {}
    runtime_route = resolve_model_route(
        packet["handoff"]["entity_type"],
        packet["handoff"].get("to_profile_id"),
    )
    merged_route = dict(packet_route)
    merged_route.update(runtime_route)
    if not merged_route.get("prompt_pack_rel_path"):
        merged_route["prompt_pack_rel_path"] = packet_route.get("prompt_pack_rel_path")
    return packet_route, merged_route


def route_drift(packet_route, runtime_route):
    drift = {}
    for field in ROUTE_AUDIT_FIELDS:
        packet_value = packet_route.get(field)
        runtime_value = runtime_route.get(field)
        if packet_value != runtime_value:
            drift[field] = {"packet": packet_value, "runtime": runtime_value}

    packet_readiness = packet_route.get("provider_readiness") or {}
    runtime_readiness = runtime_route.get("provider_readiness") or {}
    readiness_drift = {}
    for field in READINESS_AUDIT_FIELDS:
        packet_value = packet_readiness.get(field)
        runtime_value = runtime_readiness.get(field)
        if packet_value != runtime_value:
            readiness_drift[field] = {"packet": packet_value, "runtime": runtime_value}

    if readiness_drift:
        drift["provider_readiness"] = readiness_drift
    return drift


def render_task_input(packet, route):
    handoff = packet["handoff"]
    source_entry = packet.get("source_entry") or {}
    lines = [
        "## Task Context",
        "",
        f"- handoff_id: `{handoff['handoff_id']}`",
        f"- entity_type: `{handoff['entity_type']}`",
        f"- entity_id: `{handoff['entity_id']}`",
        f"- required_action: `{handoff.get('required_action') or ''}`",
        f"- task_kind: `{route.get('task_kind') or ''}`",
        f"- output_contract: `{route.get('output_contract') or ''}`",
        f"- packet_mode: `{route.get('packet_mode') or ''}`",
        "",
    ]

    if source_entry:
        lines.extend(
            [
                "## Source Entry",
                "",
                f"- registry_entry_id: `{source_entry.get('id') or ''}`",
                f"- source_status: `{source_entry.get('status') or ''}`",
                f"- source_script: `{source_entry.get('source') or ''}`",
                f"- source_created_at: `{source_entry.get('created_at') or ''}`",
                f"- snapshot_index: `{source_entry.get('snapshot_index') or ''}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Safety Rules",
            "",
            "- 当前是 shadow execution（影子执行），不能直接修改任何正式真相层。",
            "- 只能生成候选输出或执行留痕。",
            "- 不得自动批准真实研究 draft。",
            "- 不得自动导入正式 wiki。",
            "- 不得直接修改仓位、风控真相、正式调度板。",
            "",
            "## Source Documents",
            "",
        ]
    )

    source_documents = packet.get("source_documents") or []
    if not source_documents:
        lines.append("- 当前没有 source documents（源文档）预览。")
        lines.append("")

    for item in source_documents:
        lines.extend(
            [
                f"### {item.get('rel_path') or ''}",
                "",
                f"- exists: `{item.get('exists', False)}`",
                "",
            ]
        )
        preview = item.get("preview") or ""
        if preview:
            lines.append("```text")
            lines.append(preview)
            lines.append("```")
            lines.append("")

    lines.extend(
        [
            "## Requested Output Shape",
            "",
            "- 使用中文输出。",
            "- 按下面 4 段组织内容：`事实`、`解释`、`建议动作`、`不确定性`。",
            "- 所有结论都必须能回溯到上面的 source documents（源文档）。",
            "- 如果证据不足，要明确写不确定性，不要补脑。",
            "",
        ]
    )
    return "\n".join(lines)


def render_compiled_prompt(packet, route, prompt_pack_text, task_input_text, route_drift_info):
    lines = [
        f"# Shadow Prompt Bundle: {packet.get('packet_id')}",
        "",
        "## System Prompt",
        "",
        prompt_pack_text.strip() or "(missing prompt pack)",
        "",
        "## Runtime Route",
        "",
        f"- route_status: `{route.get('route_status') or ''}`",
        f"- global_mode: `{route.get('global_mode') or ''}`",
        f"- route_global_mode: `{route.get('route_global_mode') or ''}`",
        f"- task_kind: `{route.get('task_kind') or ''}`",
        f"- model_slot: `{route.get('model_slot') or ''}`",
        f"- packet_mode: `{route.get('packet_mode') or ''}`",
        f"- provider: `{route.get('provider') or ''}`",
        f"- model: `{route.get('model') or ''}`",
        f"- reasoning_effort: `{route.get('reasoning_effort') or ''}`",
        f"- output_contract: `{route.get('output_contract') or ''}`",
        "",
    ]

    if route_drift_info:
        lines.extend(
            [
                "## Packet Route Drift",
                "",
                "```json",
                json.dumps(route_drift_info, ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## Task Input",
            "",
            task_input_text.strip(),
            "",
        ]
    )
    return "\n".join(lines)


def build_openai_request_payload(packet, route, prompt_pack_text, task_input_text):
    instructions = (
        prompt_pack_text.strip()
        or "你是 SMR 的影子辅助模型，只能生成中文候选内容，不能替代脚本真相层或人工审批。"
    )
    payload = {
        "model": route.get("model"),
        "instructions": instructions,
        "input": task_input_text,
        "store": False,
        "stream": True,
        "metadata": {
            "smr_packet_id": safe_metadata_value(packet.get("packet_id")),
            "smr_handoff_id": safe_metadata_value(packet["handoff"]["handoff_id"]),
            "smr_entity_type": safe_metadata_value(packet["handoff"]["entity_type"]),
            "smr_entity_id": safe_metadata_value(packet["handoff"]["entity_id"]),
            "smr_to_profile_id": safe_metadata_value(packet["handoff"].get("to_profile_id")),
            "smr_task_kind": safe_metadata_value(route.get("task_kind")),
            "smr_output_contract": safe_metadata_value(route.get("output_contract")),
        },
    }
    reasoning_effort = route.get("reasoning_effort")
    if reasoning_effort:
        payload["reasoning"] = {"effort": reasoning_effort}
    return payload


def build_anthropic_request_payload(route, prompt_pack_text, task_input_text):
    instructions = (
        prompt_pack_text.strip()
        or "你是 SMR 的影子辅助模型，只能生成中文候选内容，不能替代脚本真相层或人工审批。"
    )
    return {
        "model": route.get("model"),
        "system": instructions,
        "messages": [
            {
                "role": "user",
                "content": task_input_text,
            }
        ],
        "max_tokens": 4096,
        "stream": False,
    }


def build_chat_completions_request_payload(route, prompt_pack_text, task_input_text):
    instructions = (
        prompt_pack_text.strip()
        or "你是 SMR 的影子辅助模型，只能生成中文候选内容，不能替代脚本真相层或人工审批。"
    )
    return {
        "model": route.get("model"),
        "messages": [
            {
                "role": "system",
                "content": instructions,
            },
            {
                "role": "user",
                "content": task_input_text,
            },
        ],
        "max_tokens": 4096,
        "stream": False,
    }


def build_provider_request_payload(packet, route, prompt_pack_text, task_input_text):
    provider = route.get("provider")
    if provider == "openai":
        return build_openai_request_payload(packet, route, prompt_pack_text, task_input_text)
    if provider == "anthropic":
        return build_anthropic_request_payload(route, prompt_pack_text, task_input_text)
    if provider == "minimax":
        if (route.get("provider_readiness") or {}).get("api_style") == "anthropic_messages":
            return build_anthropic_request_payload(route, prompt_pack_text, task_input_text)
        return build_chat_completions_request_payload(route, prompt_pack_text, task_input_text)
    return {
        "provider": provider,
        "unsupported": True,
        "task_input": task_input_text,
    }


def blocked_reason(gate_status):
    mapping = {
        "skipped_disabled": "当前全局模型模式仍是 disabled（关闭），本次没有发起真实模型请求。",
        "blocked_route": "模型路由不完整，当前无法进入影子执行。",
        "blocked_packet_mode": "当前任务包不是 shadow（影子）模式，不允许用影子执行器发请求。",
        "blocked_global_mode": "当前全局模型模式不是 shadow/canary（影子/金丝雀）之一，影子执行器不会发请求。",
        "blocked_route_mode": "当前路由模式不是 shadow/canary（影子/金丝雀）之一，影子执行器不会发请求。",
        "blocked_provider_unsupported": "当前路由 provider 或 API 风格还没有被影子执行器实现。",
        "blocked_provider_api_style": "当前 provider API 风格和目标运行时不匹配，影子执行器不会发请求。",
        "blocked_provider_disabled": "目标 provider 仍然是禁用状态，不能发起真实请求。",
        "blocked_missing_api_key": "目标 provider 已打开，但没有检测到 API key（密钥），因此没有发起真实请求。",
    }
    return mapping.get(gate_status, "当前门禁未通过，因此没有发起真实模型请求。")


def render_response_text(packet, gate_status, execution_status, api_result):
    error_detail = provider_error_detail(api_result)
    lines = [
        f"# Shadow Response Text: {packet.get('packet_id')}",
        "",
        f"- gate_status: `{gate_status}`",
        f"- execution_status: `{execution_status}`",
        "",
    ]

    if execution_status == "shadow_call_succeeded":
        output_text = (api_result or {}).get("output_text") or ""
        lines.extend(["## Model Output", "", output_text.strip() or "(empty output)", ""])
        return "\n".join(lines)

    if execution_status == "shadow_call_failed":
        lines.extend(
            [
                "## Failure Detail",
                "",
                f"- http_status: `{(api_result or {}).get('status_code')}`",
                f"- endpoint: `{(api_result or {}).get('endpoint') or ''}`",
                f"- provider_error_code: `{error_detail.get('code') or ''}`",
                f"- provider_error_reason: `{error_detail.get('reason') or ''}`",
                "",
            ]
        )
        error_text = truncate_text(error_detail.get("message") or "")
        if error_text:
            lines.extend(["```text", error_text, "```", ""])
        return "\n".join(lines)

    lines.extend(["## Outcome", "", f"- {blocked_reason(gate_status)}", ""])
    return "\n".join(lines)


def render_shadow_result(
    packet,
    route,
    gate_status,
    execution_status,
    compiled_prompt_rel_path,
    request_json_rel_path,
    response_json_rel_path,
    response_text_rel_path,
    route_drift_info,
    api_result,
):
    readiness = route.get("provider_readiness") or {}
    error_detail = provider_error_detail(api_result)
    lines = [
        f"# Shadow Execution Result: {packet.get('packet_id')}",
        "",
        f"- gate_status: `{gate_status}`",
        f"- execution_status: `{execution_status}`",
        f"- handoff_id: `{packet['handoff']['handoff_id']}`",
        f"- compiled_prompt_rel_path: `{compiled_prompt_rel_path}`",
        f"- request_json_rel_path: `{request_json_rel_path}`",
        f"- response_json_rel_path: `{response_json_rel_path}`",
        f"- response_text_rel_path: `{response_text_rel_path}`",
        f"- provider: `{route.get('provider') or ''}`",
        f"- model: `{route.get('model') or ''}`",
        f"- global_mode: `{route.get('global_mode') or ''}`",
        f"- route_global_mode: `{route.get('route_global_mode') or ''}`",
        f"- provider_enabled: `{readiness.get('enabled', False)}`",
        f"- api_key_present: `{readiness.get('has_api_key', False)}`",
        "",
        "## Outcome",
        "",
    ]

    if execution_status == "shadow_call_succeeded":
        lines.extend(
            [
                f"- 已按当前运行时配置发起真实 `{route.get('provider') or 'unknown'}` shadow 请求。",
                "- 本次仍然只写候选层与执行留痕，没有触碰任何真相层。",
                f"- http_status: `{(api_result or {}).get('status_code')}`",
                f"- endpoint: `{(api_result or {}).get('endpoint') or ''}`",
            ]
        )
        output_preview = truncate_text((api_result or {}).get("output_text") or "")
        if output_preview:
            lines.extend(["", "## Output Preview", "", output_preview])
    elif execution_status == "shadow_call_failed":
        lines.extend(
            [
                "- 已满足前门禁并尝试发起真实 shadow 请求，但请求失败。",
                "- 真相层没有任何改动，后续可根据 `response.json` 和 `response_text.md` 排查。",
                f"- http_status: `{(api_result or {}).get('status_code')}`",
                f"- endpoint: `{(api_result or {}).get('endpoint') or ''}`",
                f"- provider_error_code: `{error_detail.get('code') or ''}`",
                f"- provider_error_reason: `{error_detail.get('reason') or ''}`",
            ]
        )
        error_preview = truncate_text(error_detail.get("message") or "")
        if error_preview:
            lines.extend(["", "## Error Preview", "", error_preview])
    else:
        lines.append(f"- {blocked_reason(gate_status)}")

    if route_drift_info:
        lines.extend(
            [
                "",
                "## Runtime Drift",
                "",
                "```json",
                json.dumps(route_drift_info, ensure_ascii=False, indent=2),
                "```",
            ]
        )

    lines.append("")
    return "\n".join(lines)


def response_payload_id(api_result):
    payload = (api_result or {}).get("payload")
    if not isinstance(payload, dict):
        return None
    return payload.get("id")


def provider_error_detail(api_result):
    payload = (api_result or {}).get("payload")
    if not isinstance(payload, dict):
        payload = {}

    error_obj = payload.get("error") if isinstance(payload.get("error"), dict) else {}
    code = error_obj.get("code") or payload.get("code")
    reason = error_obj.get("reason") or payload.get("reason")
    message = error_obj.get("message") or payload.get("message")

    fallback_error = (api_result or {}).get("error")
    if not message and fallback_error:
        message = fallback_error
    if message and not isinstance(message, str):
        message = json.dumps(message, ensure_ascii=False)

    if not reason and message:
        match = re.search(r'reason="?([A-Z0-9_]+)"?', message)
        if match:
            reason = match.group(1)

    return {
        "code": code,
        "reason": reason,
        "message": message,
    }


def build_response_record(
    packet,
    route,
    gate_status,
    execution_status,
    packet_rel_path,
    compiled_prompt_rel_path,
    request_json_rel_path,
    response_text_rel_path,
    route_drift_info,
    api_result,
):
    api_result = api_result or {}
    error_detail = provider_error_detail(api_result)
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "packet_id": packet.get("packet_id"),
        "handoff_id": packet["handoff"]["handoff_id"],
        "entity_type": packet["handoff"].get("entity_type"),
        "entity_id": packet["handoff"].get("entity_id"),
        "to_profile_id": packet["handoff"].get("to_profile_id"),
        "packet_rel_path": packet_rel_path,
        "gate_status": gate_status,
        "execution_status": execution_status,
        "attempted_call": gate_status == "ready_for_shadow_call",
        "provider": route.get("provider"),
        "model": route.get("model"),
        "reasoning_effort": route.get("reasoning_effort"),
        "global_mode": route.get("global_mode"),
        "route_global_mode": route.get("route_global_mode"),
        "compiled_prompt_rel_path": compiled_prompt_rel_path,
        "request_json_rel_path": request_json_rel_path,
        "response_text_rel_path": response_text_rel_path,
        "http_status": api_result.get("status_code"),
        "ok": api_result.get("ok"),
        "endpoint": api_result.get("endpoint"),
        "response_id": response_payload_id(api_result),
        "output_text_chars": len((api_result.get("output_text") or "").strip()),
        "error": error_detail.get("message"),
        "provider_error_code": error_detail.get("code"),
        "provider_error_reason": error_detail.get("reason"),
        "route_drift": route_drift_info,
        "provider_readiness": route.get("provider_readiness") or {},
        "response_payload": api_result.get("payload"),
    }


def main():
    parser = argparse.ArgumentParser(description="Run SMR model shadow compilation")
    parser.add_argument("--handoff-id", help="Existing handoff id with a generated model_task_packet")
    parser.add_argument("--packet-rel-path", help="Explicit packet json rel_path")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.handoff_id and not args.packet_rel_path:
        raise SystemExit("Either --handoff-id or --packet-rel-path is required")

    conn = sqlite3.connect(DB_PATH)
    if args.packet_rel_path:
        packet = load_packet(args.packet_rel_path)
        packet_rel_path = args.packet_rel_path
        handoff = get_handoff(packet["handoff"]["handoff_id"])
    else:
        packet, packet_rel_path = load_packet_from_handoff(conn, args.handoff_id)
        handoff = get_handoff(args.handoff_id)

    packet_route, route = resolve_runtime_route(packet)
    route_drift_info = route_drift(packet_route, route)

    to_profile_id = packet["handoff"]["to_profile_id"]
    profile = get_profile(to_profile_id)
    workspace = profile_workspace_path(profile)
    shadow_dir = workspace / "shadow_runs"
    stem = packet["packet_id"]
    compiled_prompt_path = shadow_dir / f"{stem}__compiled_prompt.md"
    request_json_path = shadow_dir / f"{stem}__request.json"
    response_json_path = shadow_dir / f"{stem}__response.json"
    response_text_path = shadow_dir / f"{stem}__response_text.md"
    result_md_path = shadow_dir / f"{stem}__result.md"

    prompt_pack_text = load_prompt_pack(route.get("prompt_pack_rel_path"))
    task_input_text = render_task_input(packet, route)
    compiled_prompt_text = render_compiled_prompt(
        packet,
        route,
        prompt_pack_text,
        task_input_text,
        route_drift_info,
    )
    gate_status = shadow_execution_status(route)
    request_payload = build_provider_request_payload(packet, route, prompt_pack_text, task_input_text)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "gate_status": gate_status,
                    "route_drift": route_drift_info,
                    "request_payload": request_payload,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        conn.close()
        return

    shadow_dir.mkdir(parents=True, exist_ok=True)
    compiled_prompt_path.write_text(compiled_prompt_text + "\n", encoding="utf-8")
    request_json_path.write_text(json.dumps(request_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    api_result = {
        "ok": False,
        "status_code": None,
        "headers": {},
        "endpoint": None,
        "payload": None,
        "output_text": "",
        "error": None,
    }
    execution_status = gate_status
    if gate_status == "ready_for_shadow_call":
        try:
            provider = route.get("provider")
            if provider == "openai":
                api_result = call_openai_responses_api(
                    request_payload,
                    route.get("provider_readiness") or {},
                    client_request_id=packet.get("packet_id"),
                )
            elif provider == "anthropic":
                api_result = call_anthropic_messages_api(
                    request_payload,
                    route.get("provider_readiness") or {},
                    client_request_id=packet.get("packet_id"),
                )
            elif provider == "minimax":
                readiness = route.get("provider_readiness") or {}
                if readiness.get("api_style") == "anthropic_messages":
                    api_result = call_anthropic_messages_api(
                        request_payload,
                        readiness,
                        client_request_id=packet.get("packet_id"),
                    )
                else:
                    api_result = call_minimax_chat_completions_api(
                        request_payload,
                        readiness,
                        client_request_id=packet.get("packet_id"),
                    )
            else:
                api_result = {
                    "ok": False,
                    "status_code": None,
                    "headers": {},
                    "endpoint": None,
                    "payload": None,
                    "output_text": "",
                    "error": f"Unsupported provider: {provider}",
                }
        except Exception as exc:
            api_result = {
                "ok": False,
                "status_code": None,
                "headers": {},
                "endpoint": None,
                "payload": None,
                "output_text": "",
                "error": str(exc),
            }
        execution_status = "shadow_call_succeeded" if api_result.get("ok") else "shadow_call_failed"

    compiled_prompt_rel_path = relative_to_project(compiled_prompt_path)
    request_json_rel_path = relative_to_project(request_json_path)
    response_text_rel_path = relative_to_project(response_text_path)
    response_record = build_response_record(
        packet,
        route,
        gate_status,
        execution_status,
        packet_rel_path,
        compiled_prompt_rel_path,
        request_json_rel_path,
        response_text_rel_path,
        route_drift_info,
        api_result,
    )
    response_json_path.write_text(json.dumps(response_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    response_json_rel_path = relative_to_project(response_json_path)

    response_text = render_response_text(packet, gate_status, execution_status, api_result)
    response_text_path.write_text(response_text + "\n", encoding="utf-8")

    result_text = render_shadow_result(
        packet,
        route,
        gate_status,
        execution_status,
        compiled_prompt_rel_path,
        request_json_rel_path,
        response_json_rel_path,
        response_text_rel_path,
        route_drift_info,
        api_result,
    )
    result_md_path.write_text(result_text + "\n", encoding="utf-8")

    registry_entry = register_snapshot(
        conn,
        entity_type="model_shadow_execution",
        entity_id=handoff["handoff_id"],
        status=execution_status,
        source="run_model_shadow.py",
        relationships={
            "handoff_id": handoff["handoff_id"],
            "entity_type": handoff["entity_type"],
            "entity_id": handoff["entity_id"],
            "to_profile_id": to_profile_id,
        },
        payload={
            "packet_rel_path": packet_rel_path,
            "compiled_prompt_rel_path": compiled_prompt_rel_path,
            "request_json_rel_path": request_json_rel_path,
            "response_json_rel_path": response_json_rel_path,
            "response_text_rel_path": response_text_rel_path,
            "result_md_rel_path": relative_to_project(result_md_path),
            "gate_status": gate_status,
            "provider": route.get("provider"),
            "model": route.get("model"),
            "packet_mode": route.get("packet_mode"),
            "attempted_call": gate_status == "ready_for_shadow_call",
            "http_status": api_result.get("status_code"),
            "response_id": response_payload_id(api_result),
            "provider_error_code": provider_error_detail(api_result).get("code"),
            "provider_error_reason": provider_error_detail(api_result).get("reason"),
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "run_model_shadow.py",
        "success",
        "model shadow execution recorded",
        {
            "handoff_id": handoff["handoff_id"],
            "entity_type": handoff["entity_type"],
            "entity_id": handoff["entity_id"],
            "gate_status": gate_status,
            "execution_status": execution_status,
            "compiled_prompt_rel_path": compiled_prompt_rel_path,
            "request_json_rel_path": request_json_rel_path,
            "response_json_rel_path": response_json_rel_path,
            "response_text_rel_path": response_text_rel_path,
            "result_md_rel_path": relative_to_project(result_md_path),
            "registry_entry_id": registry_entry["id"],
        },
    )
    print(f"Model shadow execution: {handoff['handoff_id']}")
    print(f"  gate_status={gate_status}")
    print(f"  execution_status={execution_status}")
    print(f"  compiled_prompt_rel_path={compiled_prompt_rel_path}")
    print(f"  request_json_rel_path={request_json_rel_path}")
    print(f"  response_json_rel_path={response_json_rel_path}")
    print(f"  response_text_rel_path={response_text_rel_path}")
    print(f"  result_md_rel_path={relative_to_project(result_md_path)}")
    error_detail = provider_error_detail(api_result)
    if error_detail.get("code") or error_detail.get("reason"):
        print(f"  provider_error_code={error_detail.get('code') or ''}")
        print(f"  provider_error_reason={error_detail.get('reason') or ''}")


if __name__ == "__main__":
    main()
