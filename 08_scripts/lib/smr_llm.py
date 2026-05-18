#!/usr/bin/env python3
"""SMR model-runtime configuration helpers for packetized LLM integration."""

import json
import os
import re
import ssl
import urllib.error
import urllib.request
import warnings
from pathlib import Path

warnings.filterwarnings(
    "ignore",
    message="urllib3 v2 only supports OpenSSL 1.1.1+",
    category=Warning,
)

import requests

from smr_paths import env_or_project_path, normalize_project_path, project_path, relative_to_project

try:
    import certifi
except Exception:  # pragma: no cover - optional CA bundle fallback
    certifi = None

PROMPT_PACK_DIR = project_path("12_smr_agents", "prompt_packs")
SHADOW_EXECUTION_ALLOWED_MODES = {"shadow", "canary"}
CODEX_HOME = Path.home() / ".codex"
CODEX_CONFIG_PATH = CODEX_HOME / "config.toml"
CODEX_AUTH_PATH = CODEX_HOME / "auth.json"
LOCAL_ENV_PATHS = [
    project_path(".smr_env.local"),
    project_path("00_control", "local_model_env.env"),
]
_LOCAL_ENV_LOADED = False


def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def model_runtime_dir():
    return env_or_project_path("SMR_MODEL_RUNTIME_DIR", "12_smr_agents", "model_runtime")


def model_profile_path():
    return env_or_project_path("SMR_MODEL_PROFILES_PATH", "12_smr_agents", "model_runtime", "model_profiles.json")


def task_route_path():
    return env_or_project_path("SMR_TASK_ROUTES_PATH", "12_smr_agents", "model_runtime", "task_routes.json")


def load_model_profiles():
    return _load_json(model_profile_path())


def load_task_routes():
    return _load_json(task_route_path())


def load_packet(path_value):
    path = normalize_project_path(path_value)
    if path is None:
        raise FileNotFoundError("Packet path is empty")
    return _load_json(path)


def load_prompt_pack(rel_path):
    path = normalize_project_path(rel_path)
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def parse_env_line(line):
    text = line.strip()
    if not text or text.startswith("#"):
        return None, None
    if text.startswith("export "):
        text = text[len("export ") :].strip()
    if "=" not in text:
        return None, None
    key, value = text.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
        return None, None
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return key, value


def load_local_model_env():
    global _LOCAL_ENV_LOADED
    if _LOCAL_ENV_LOADED:
        return
    _LOCAL_ENV_LOADED = True
    for path in LOCAL_ENV_PATHS:
        if not path.exists():
            continue
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                key, value = parse_env_line(line)
                if key and value and key not in os.environ:
                    os.environ[key] = value
        except Exception:
            continue


def env_candidates(primary, aliases=None):
    candidates = []
    for name in [primary, *(aliases or [])]:
        if name and name not in candidates:
            candidates.append(name)
    return candidates


def first_present_env(candidates):
    load_local_model_env()
    for name in candidates:
        value = os.environ.get(name)
        if value:
            return name, value
    return None, None


def default_ssl_context():
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()


def prompt_pack_rel_path(profile_id):
    if not profile_id:
        return None
    path = PROMPT_PACK_DIR / f"{profile_id}.md"
    if not path.exists():
        return None
    return relative_to_project(path)


def provider_readiness(provider_name, profiles=None):
    profiles = profiles or load_model_profiles()
    provider = (profiles.get("providers") or {}).get(provider_name) or {}
    api_key_env = provider.get("api_key_env")
    base_url_env = provider.get("base_url_env")
    api_key_envs = env_candidates(api_key_env, provider.get("api_key_env_aliases"))
    base_url_envs = env_candidates(base_url_env, provider.get("base_url_env_aliases"))
    fallback = codex_openai_fallback() if provider_name == "openai" else {}
    resolved_api_key_env, resolved_api_key = first_present_env(api_key_envs)
    resolved_base_url_env, resolved_base_url = first_present_env(base_url_envs)
    resolved_api_key = resolved_api_key or fallback.get("api_key")
    resolved_base_url = resolved_base_url or fallback.get("base_url") or provider.get("default_base_url")
    return {
        "provider": provider_name,
        "enabled": bool(provider.get("enabled")),
        "api_key_env": api_key_env,
        "api_key_env_aliases": provider.get("api_key_env_aliases") or [],
        "api_key_env_candidates": api_key_envs,
        "resolved_api_key_env": resolved_api_key_env,
        "base_url_env": base_url_env,
        "base_url_env_aliases": provider.get("base_url_env_aliases") or [],
        "base_url_env_candidates": base_url_envs,
        "resolved_base_url_env": resolved_base_url_env,
        "default_base_url": provider.get("default_base_url"),
        "organization_env": provider.get("organization_env", "OPENAI_ORGANIZATION"),
        "project_env": provider.get("project_env", "OPENAI_PROJECT"),
        "anthropic_version": provider.get("anthropic_version", "2023-06-01"),
        "has_api_key": bool(resolved_api_key),
        "has_base_url": bool(resolved_base_url),
        "api_style": provider.get("api_style"),
        "fallback_source": fallback.get("source"),
        "fallback_base_url": fallback.get("base_url"),
        "fallback_wire_api": fallback.get("wire_api"),
    }


def resolve_model_route(entity_type, to_profile_id=None):
    profiles = load_model_profiles()
    routes = load_task_routes()
    route = (routes.get("entity_routes") or {}).get(entity_type) or {}
    slot_name = route.get("model_slot")
    slot = (profiles.get("model_slots") or {}).get(slot_name) or {}

    route_status = "configured"
    if not route:
        route_status = "missing_route"
    elif not slot:
        route_status = "missing_model_slot"
    elif to_profile_id and route.get("to_profile_id") and route.get("to_profile_id") != to_profile_id:
        route_status = "profile_mismatch"

    provider_name = slot.get("provider")
    readiness = provider_readiness(provider_name, profiles) if provider_name else {}

    return {
        "global_mode": profiles.get("global_mode", "disabled"),
        "route_global_mode": routes.get("global_mode", profiles.get("global_mode", "disabled")),
        "route_status": route_status,
        "entity_type": entity_type,
        "to_profile_id": to_profile_id,
        "task_kind": route.get("task_kind"),
        "model_slot": slot_name,
        "packet_mode": route.get("packet_mode", "shadow"),
        "requires_human_review": route.get("requires_human_review", True),
        "auto_apply": route.get("auto_apply", False),
        "output_contract": route.get("output_contract"),
        "prompt_pack_rel_path": route.get("prompt_pack_rel_path") or prompt_pack_rel_path(to_profile_id),
        "provider": provider_name,
        "model": slot.get("model"),
        "reasoning_effort": slot.get("reasoning_effort"),
        "provider_readiness": readiness,
        "intended_use": slot.get("intended_use") or [],
    }


def shadow_execution_status(route):
    if route.get("route_status") != "configured":
        return "blocked_route"

    if route.get("packet_mode") not in {None, "shadow"}:
        return "blocked_packet_mode"

    global_mode = route.get("global_mode")
    route_mode = route.get("route_global_mode")
    if global_mode == "disabled" or route_mode == "disabled":
        return "skipped_disabled"
    if global_mode not in SHADOW_EXECUTION_ALLOWED_MODES:
        return "blocked_global_mode"
    if route_mode not in SHADOW_EXECUTION_ALLOWED_MODES:
        return "blocked_route_mode"

    readiness = route.get("provider_readiness") or {}
    provider = route.get("provider")
    api_style = readiness.get("api_style")
    if provider == "openai" and api_style in {None, "responses"}:
        pass
    elif provider == "anthropic" and api_style == "messages":
        pass
    elif provider == "minimax" and api_style in {"chat_completions", "anthropic_messages"}:
        pass
    else:
        return "blocked_provider_unsupported"
    if provider == "openai" and readiness.get("api_style") not in {None, "responses"}:
        return "blocked_provider_api_style"
    if provider == "anthropic" and readiness.get("api_style") != "messages":
        return "blocked_provider_api_style"
    if provider == "minimax" and readiness.get("api_style") not in {"chat_completions", "anthropic_messages"}:
        return "blocked_provider_api_style"
    if not readiness.get("enabled"):
        return "blocked_provider_disabled"
    if not readiness.get("has_api_key"):
        return "blocked_missing_api_key"

    return "ready_for_shadow_call"


def _load_codex_auth():
    if os.environ.get("SMR_DISABLE_CODEX_OPENAI_FALLBACK") == "1":
        return {}
    if not CODEX_AUTH_PATH.exists():
        return {}
    try:
        return _load_json(CODEX_AUTH_PATH)
    except Exception:
        return {}


def _load_codex_config_text():
    if os.environ.get("SMR_DISABLE_CODEX_OPENAI_FALLBACK") == "1":
        return ""
    if not CODEX_CONFIG_PATH.exists():
        return ""
    try:
        return CODEX_CONFIG_PATH.read_text(encoding="utf-8")
    except Exception:
        return ""


def _toml_string(text, key):
    match = re.search(rf'(?m)^\s*{re.escape(key)}\s*=\s*"([^"]+)"', text)
    return match.group(1) if match else None


def _toml_bool(text, key):
    match = re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*(true|false)\s*$", text)
    if not match:
        return None
    return match.group(1) == "true"


def _toml_section(text, header):
    pattern = rf"(?ms)^\[{re.escape(header)}\]\s*(.*?)(?=^\[|\Z)"
    match = re.search(pattern, text)
    return match.group(1) if match else ""


def codex_openai_fallback():
    if os.environ.get("SMR_DISABLE_CODEX_OPENAI_FALLBACK") == "1":
        return {}

    auth = _load_codex_auth()
    api_key = auth.get("OPENAI_API_KEY")
    config_text = _load_codex_config_text()
    provider_name = _toml_string(config_text, "model_provider")
    if not provider_name:
        return {}
    section = _toml_section(config_text, f"model_providers.{provider_name}")
    if not section:
        return {}
    requires_openai_auth = _toml_bool(section, "requires_openai_auth")
    if requires_openai_auth is False:
        return {}
    base_url = _toml_string(section, "base_url")
    wire_api = _toml_string(section, "wire_api")
    if not api_key and not base_url:
        return {}
    return {
        "api_key": api_key,
        "base_url": base_url,
        "wire_api": wire_api,
        "source": "codex_local_provider",
    }


def resolved_api_key(readiness):
    _, api_key = first_present_env(readiness.get("api_key_env_candidates") or [readiness.get("api_key_env")])
    if api_key:
        return api_key
    fallback = codex_openai_fallback() if readiness.get("provider") == "openai" else {}
    return fallback.get("api_key")


def resolved_base_url(readiness):
    _, base_url = first_present_env(readiness.get("base_url_env_candidates") or [readiness.get("base_url_env")])
    if base_url:
        return base_url
    fallback = codex_openai_fallback() if readiness.get("provider") == "openai" else {}
    return fallback.get("base_url") or readiness.get("default_base_url")


def join_endpoint(base_url, path_suffix):
    base = (base_url or "").rstrip("/")
    suffix = path_suffix if path_suffix.startswith("/") else "/" + path_suffix
    if not base:
        return suffix
    if base.endswith(suffix):
        return base
    if base.endswith("/v1") and suffix.startswith("/v1/"):
        return base + suffix[3:]
    return base + suffix


def provider_endpoint(readiness, default_endpoint, path_suffix):
    configured = resolved_base_url(readiness)
    if not configured:
        return default_endpoint
    return join_endpoint(configured, path_suffix)


def parse_json_or_none(raw_text):
    try:
        return json.loads(raw_text)
    except Exception:
        return None


def extract_openai_output_text(payload):
    if not isinstance(payload, dict):
        return ""
    if payload.get("output_text"):
        return payload["output_text"]

    chunks = []
    for item in payload.get("output", []) or []:
        for content in item.get("content", []) or []:
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(content["text"])
    return "\n\n".join(chunks).strip()


def extract_anthropic_output_text(payload):
    if not isinstance(payload, dict):
        return ""
    chunks = []
    for item in payload.get("content", []) or []:
        if item.get("type") == "text" and item.get("text"):
            chunks.append(item["text"])
    return "\n\n".join(chunks).strip()


def extract_chat_completion_output_text(payload):
    if not isinstance(payload, dict):
        return ""
    chunks = []
    for choice in payload.get("choices", []) or []:
        message = choice.get("message") or {}
        content = message.get("content")
        if content:
            chunks.append(content)
    return "\n\n".join(chunks).strip()


def read_openai_sse_lines(lines):
    event_name = None
    data_lines = []
    last_response = None
    output_chunks = []
    saw_delta = False

    def flush_event():
        nonlocal event_name, data_lines, last_response, saw_delta
        if not data_lines:
            event_name = None
            return False

        data_text = "\n".join(data_lines).strip()
        event_name = None
        data_lines = []

        if not data_text or data_text == "[DONE]":
            return data_text == "[DONE]"

        payload = parse_json_or_none(data_text)
        if not isinstance(payload, dict):
            return False

        response_obj = payload.get("response")
        if isinstance(response_obj, dict):
            last_response = response_obj

        payload_type = payload.get("type")
        if payload_type == "response.output_text.delta" and payload.get("delta"):
            output_chunks.append(payload["delta"])
            saw_delta = True
        elif payload_type == "response.output_text.done" and payload.get("text") and not saw_delta:
            output_chunks.append(payload["text"])
        return False

    for line in lines:
        if isinstance(line, bytes):
            decoded = line.decode("utf-8", errors="replace").rstrip("\r\n")
        else:
            decoded = str(line).rstrip("\r\n")
        if not decoded:
            if flush_event():
                break
            continue
        if decoded.startswith(":"):
            continue
        if decoded.startswith("event:"):
            event_name = decoded[6:].strip() or None
            continue
        if decoded.startswith("data:"):
            data_lines.append(decoded[5:].lstrip())
            continue
    else:
        flush_event()

    output_text = "".join(output_chunks).strip()
    if not output_text:
        output_text = extract_openai_output_text(last_response)
    return last_response, output_text


def call_openai_responses_api(request_payload, readiness, client_request_id=None, timeout=180):
    api_key = resolved_api_key(readiness)
    if not api_key:
        raise RuntimeError(f"Missing OpenAI API key env: {readiness.get('api_key_env')}")

    endpoint = provider_endpoint(
        readiness,
        "https://api.openai.com/v1/responses",
        "/responses",
    )
    payload = dict(request_payload or {})
    payload["stream"] = True
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream",
    }

    organization_env = readiness.get("organization_env")
    project_env = readiness.get("project_env")
    if organization_env and os.environ.get(organization_env):
        headers["OpenAI-Organization"] = os.environ[organization_env]
    if project_env and os.environ.get(project_env):
        headers["OpenAI-Project"] = os.environ[project_env]
    if client_request_id:
        headers["X-Client-Request-Id"] = client_request_id[:512]

    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            stream=True,
            timeout=timeout,
        )
        if response.ok:
            response_payload, output_text = read_openai_sse_lines(response.iter_lines())
            return {
                "ok": True,
                "status_code": response.status_code,
                "headers": dict(response.headers.items()),
                "endpoint": endpoint,
                "payload": response_payload,
                "output_text": output_text,
                "error": None,
            }

        raw = response.content.decode("utf-8", errors="replace")
        payload = parse_json_or_none(raw)
        return {
            "ok": False,
            "status_code": response.status_code,
            "headers": dict(response.headers.items()),
            "endpoint": endpoint,
            "payload": payload,
            "output_text": "",
            "error": raw or f"HTTP {response.status_code}",
        }
    except Exception as exc:
        return {
            "ok": False,
            "status_code": None,
            "headers": {},
            "endpoint": endpoint,
            "payload": None,
            "output_text": "",
            "error": str(exc),
        }


def call_anthropic_messages_api(request_payload, readiness, client_request_id=None, timeout=180):
    api_key = resolved_api_key(readiness)
    if not api_key:
        raise RuntimeError(f"Missing Anthropic API key env: {readiness.get('api_key_env')}")

    endpoint = provider_endpoint(
        readiness,
        "https://api.anthropic.com/v1/messages",
        "/v1/messages",
    )
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": readiness.get("anthropic_version") or "2023-06-01",
        "Accept": "application/json",
    }
    if client_request_id:
        headers["x-client-request-id"] = client_request_id[:512]

    body = json.dumps(request_payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=timeout, context=default_ssl_context()) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw)
            return {
                "ok": True,
                "status_code": response.getcode(),
                "headers": dict(response.headers.items()),
                "endpoint": endpoint,
                "payload": payload,
                "output_text": extract_anthropic_output_text(payload),
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        payload = parse_json_or_none(raw)
        return {
            "ok": False,
            "status_code": exc.code,
            "headers": dict(exc.headers.items()) if exc.headers else {},
            "endpoint": endpoint,
            "payload": payload,
            "output_text": "",
            "error": raw or str(exc),
        }
    except Exception as exc:
        return {
            "ok": False,
            "status_code": None,
            "headers": {},
            "endpoint": endpoint,
            "payload": None,
            "output_text": "",
            "error": str(exc),
        }


def call_minimax_chat_completions_api(request_payload, readiness, client_request_id=None, timeout=180):
    api_key = resolved_api_key(readiness)
    if not api_key:
        raise RuntimeError(f"Missing MiniMax API key env: {readiness.get('api_key_env')}")

    endpoint = provider_endpoint(
        readiness,
        "https://api.minimax.io/v1/chat/completions",
        "/chat/completions",
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    if client_request_id:
        headers["X-Client-Request-Id"] = client_request_id[:512]

    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=request_payload,
            timeout=timeout,
        )
        raw = response.content.decode("utf-8", errors="replace")
        payload = parse_json_or_none(raw)
        return {
            "ok": response.ok,
            "status_code": response.status_code,
            "headers": dict(response.headers.items()),
            "endpoint": endpoint,
            "payload": payload,
            "output_text": extract_chat_completion_output_text(payload) if response.ok else "",
            "error": None if response.ok else (raw or f"HTTP {response.status_code}"),
        }
    except Exception as exc:
        return {
            "ok": False,
            "status_code": None,
            "headers": {},
            "endpoint": endpoint,
            "payload": None,
            "output_text": "",
            "error": str(exc),
        }
