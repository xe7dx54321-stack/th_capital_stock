#!/usr/bin/env python3
"""Unified fetch helpers with optional Scrapling support."""

import hashlib
import json
import re
import ssl
import urllib.parse
import urllib.request
from functools import lru_cache
from pathlib import Path

from smr_paths import project_path

DEFAULT_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
DEFAULT_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
DEFAULT_POLICY_PATH = project_path("00_control", "source_fetch_policy.json")

ENGINE_ALIASES = {
    "auto": None,
    "legacy": ["urllib"],
    "urllib": ["urllib"],
    "static": ["scrapling_static"],
    "scrapling-static": ["scrapling_static"],
    "scrapling_static": ["scrapling_static"],
    "dynamic": ["scrapling_dynamic"],
    "scrapling-dynamic": ["scrapling_dynamic"],
    "scrapling_dynamic": ["scrapling_dynamic"],
    "stealth": ["scrapling_stealth"],
    "scrapling-stealth": ["scrapling_stealth"],
    "scrapling_stealth": ["scrapling_stealth"],
}

GENERIC_BLOCK_MARKERS = (
    "access denied",
    "request blocked",
    "too many requests",
    "verify you are human",
    "checking your browser",
    "enable javascript and cookies",
    "cf-chl",
    "cf-browser-verification",
    "cloudflare ray id",
    "captcha",
)


class FetchError(RuntimeError):
    def __init__(self, message, attempts=None):
        super().__init__(message)
        self.attempts = attempts or []


@lru_cache(maxsize=1)
def load_fetch_policy(path_value=None):
    path = Path(path_value or DEFAULT_POLICY_PATH)
    if not path.exists():
        return {
            "default": {
                "fetch_order": ["scrapling_static", "urllib"],
                "blocked_markers": list(GENERIC_BLOCK_MARKERS),
            },
            "domains": {},
        }
    return json.loads(path.read_text(encoding="utf-8"))


def clear_fetch_policy_cache():
    load_fetch_policy.cache_clear()


def host_key(url):
    return urllib.parse.urlparse(str(url or "")).netloc.lower()


def domain_matches(host, domain):
    host = str(host or "").lower()
    domain = str(domain or "").lower().lstrip(".")
    return host == domain or host.endswith(f".{domain}")


def fetch_policy_for_url(url, path_value=None):
    raw_policy = load_fetch_policy(path_value)
    policy = dict(raw_policy.get("default") or {})
    matched_domain = ""
    host = host_key(url)
    for domain, domain_policy in sorted((raw_policy.get("domains") or {}).items(), key=lambda item: len(item[0])):
        if domain_matches(host, domain):
            policy.update(domain_policy or {})
            matched_domain = domain
    policy.setdefault("fetch_order", ["scrapling_static", "urllib"])
    policy.setdefault("blocked_markers", list(GENERIC_BLOCK_MARKERS))
    policy["matched_domain"] = matched_domain
    return policy


def normalize_engine(engine):
    return str(engine or "").strip().lower().replace("-", "_")


def resolve_fetch_order(mode, policy):
    normalized_mode = str(mode or "auto").strip().lower()
    if normalized_mode not in ENGINE_ALIASES:
        raise ValueError(f"unsupported fetch mode: {mode}")
    if normalized_mode == "auto":
        order = policy.get("fetch_order") or ["scrapling_static", "urllib"]
    else:
        order = ENGINE_ALIASES[normalized_mode]
    normalized_order = [normalize_engine(engine) for engine in order if str(engine or "").strip()]
    if not normalized_order:
        normalized_order = ["urllib"]
    return normalized_order


def build_headers(user_agent=None, accept=None, extra_headers=None, referer=None):
    headers = {
        "User-Agent": user_agent or DEFAULT_BROWSER_USER_AGENT,
        "Accept": accept or DEFAULT_ACCEPT,
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    if referer:
        headers["Referer"] = referer
    headers.update(extra_headers or {})
    return {key: value for key, value in headers.items() if value is not None}


def content_type_from_headers(headers):
    for key, value in (headers or {}).items():
        if str(key).lower() == "content-type":
            return str(value or "")
    return ""


def decode_body(raw_bytes, content_type="", encoding=None):
    charset = encoding
    if not charset:
        match = re.search(r"charset=([A-Za-z0-9._-]+)", str(content_type or ""), flags=re.I)
        if match:
            charset = match.group(1)
    for candidate in (charset, "utf-8", "utf-8-sig", "gb18030", "latin-1"):
        if not candidate:
            continue
        try:
            return raw_bytes.decode(candidate)
        except UnicodeDecodeError:
            continue
    return raw_bytes.decode("utf-8", errors="replace")


def response_extension(response):
    final_url = response.get("final_url") or ""
    suffix = Path(urllib.parse.urlparse(final_url).path).suffix.lower()
    if suffix:
        return suffix
    content_type = str(response.get("content_type") or "").lower()
    if "json" in content_type:
        return ".json"
    if "pdf" in content_type:
        return ".pdf"
    if "xml" in content_type:
        return ".xml"
    if "html" in content_type:
        return ".html"
    if "plain" in content_type or "text" in content_type:
        return ".txt"
    return ".bin"


def response_domain(response):
    return host_key(response.get("final_url") or "")


def default_ssl_context():
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def build_result(*, requested_url, final_url, status_code, headers, raw_bytes, engine, rendered, encoding=None):
    headers = dict(headers or {})
    content_type = content_type_from_headers(headers)
    raw_bytes = raw_bytes or b""
    text = decode_body(raw_bytes, content_type, encoding=encoding)
    return {
        "requested_url": requested_url,
        "final_url": final_url or requested_url,
        "status_code": status_code,
        "headers": headers,
        "content_type": content_type,
        "bytes": raw_bytes,
        "raw_bytes": raw_bytes,
        "text": text,
        "fetch_engine": engine,
        "rendered": bool(rendered),
        "content_hash": hashlib.sha256(raw_bytes).hexdigest(),
    }


def fetch_with_urllib(url, *, timeout, headers):
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout, context=default_ssl_context()) as response:
        raw_bytes = response.read()
        return build_result(
            requested_url=url,
            final_url=response.geturl(),
            status_code=response.getcode(),
            headers=dict(response.headers.items()),
            raw_bytes=raw_bytes,
            engine="urllib",
            rendered=False,
        )


def fetch_with_scrapling_static(url, *, timeout, headers, policy):
    try:
        from scrapling.fetchers import Fetcher
    except Exception as exc:
        raise FetchError(f"scrapling is not available: {exc}") from exc

    page = Fetcher.get(
        url,
        timeout=timeout,
        headers=headers,
        retries=int(policy.get("retries", 2)),
        retry_delay=float(policy.get("retry_delay", 1)),
        follow_redirects=policy.get("follow_redirects", "safe"),
        impersonate=policy.get("impersonate", "chrome"),
        stealthy_headers=bool(policy.get("stealthy_headers", True)),
    )
    return result_from_scrapling_page(url, page, "scrapling_static", rendered=False)


def fetch_with_scrapling_browser(url, *, engine, timeout, headers, policy, wait_selector=None):
    try:
        from scrapling.fetchers import DynamicFetcher, StealthyFetcher
    except Exception as exc:
        raise FetchError(f"scrapling browser fetchers are not available: {exc}") from exc

    fetcher = DynamicFetcher if engine == "scrapling_dynamic" else StealthyFetcher
    kwargs = {
        "headless": bool(policy.get("headless", True)),
        "disable_resources": bool(policy.get("disable_resources", True)),
        "network_idle": bool(policy.get("network_idle", True)),
        "load_dom": bool(policy.get("load_dom", True)),
        "timeout": int(float(timeout) * 1000),
        "retries": int(policy.get("browser_retries", 1)),
        "retry_delay": float(policy.get("retry_delay", 1)),
        "google_search": bool(policy.get("google_search", False)),
        "real_chrome": bool(policy.get("real_chrome", True)),
        "extra_headers": headers,
        "useragent": headers.get("User-Agent"),
    }
    selector = wait_selector or policy.get("wait_selector")
    if selector:
        kwargs["wait_selector"] = selector
        kwargs["wait_selector_state"] = policy.get("wait_selector_state", "attached")
    blocked_domains = policy.get("blocked_domains")
    if blocked_domains:
        kwargs["blocked_domains"] = set(blocked_domains)
    if engine == "scrapling_stealth":
        kwargs.update(
            {
                "solve_cloudflare": bool(policy.get("solve_cloudflare", False)),
                "block_webrtc": bool(policy.get("block_webrtc", True)),
                "hide_canvas": bool(policy.get("hide_canvas", False)),
                "allow_webgl": bool(policy.get("allow_webgl", False)),
            }
        )
    page = fetcher.fetch(url, **kwargs)
    return result_from_scrapling_page(url, page, engine, rendered=True)


def result_from_scrapling_page(requested_url, page, engine, rendered):
    headers = dict(getattr(page, "headers", {}) or {})
    return build_result(
        requested_url=requested_url,
        final_url=getattr(page, "url", requested_url),
        status_code=getattr(page, "status", None),
        headers=headers,
        raw_bytes=getattr(page, "body", b"") or b"",
        engine=engine,
        rendered=rendered,
        encoding=getattr(page, "encoding", None),
    )


def response_warning(result, policy):
    status_code = result.get("status_code")
    if status_code in set(policy.get("retry_status_codes") or [403, 408, 409, 425, 429, 500, 502, 503, 504]):
        return f"retryable_status:{status_code}"

    min_text_chars = int(policy.get("min_text_chars") or 0)
    if min_text_chars and len((result.get("text") or "").strip()) < min_text_chars:
        return f"short_text:{len((result.get('text') or '').strip())}"

    text_lower = (result.get("text") or "").lower()
    for marker in policy.get("blocked_markers") or GENERIC_BLOCK_MARKERS:
        marker_text = str(marker or "").strip().lower()
        if marker_text and marker_text in text_lower:
            return f"blocked_marker:{marker_text[:40]}"
    return ""


def fetch_url(
    url,
    *,
    timeout=30,
    mode="auto",
    user_agent=None,
    accept=None,
    extra_headers=None,
    wait_selector=None,
    policy_path=None,
):
    policy = fetch_policy_for_url(url, policy_path)
    headers = build_headers(
        user_agent=user_agent,
        accept=accept,
        extra_headers=extra_headers,
        referer=policy.get("referer"),
    )
    order = resolve_fetch_order(mode, policy)
    attempts = []
    last_warning_result = None

    for index, engine in enumerate(order):
        try:
            if engine == "urllib":
                result = fetch_with_urllib(url, timeout=timeout, headers=headers)
            elif engine == "scrapling_static":
                result = fetch_with_scrapling_static(url, timeout=timeout, headers=headers, policy=policy)
            elif engine in {"scrapling_dynamic", "scrapling_stealth"}:
                result = fetch_with_scrapling_browser(
                    url,
                    engine=engine,
                    timeout=timeout,
                    headers=headers,
                    policy=policy,
                    wait_selector=wait_selector,
                )
            else:
                raise ValueError(f"unsupported fetch engine: {engine}")

            warning = response_warning(result, policy)
            attempt = {
                "engine": engine,
                "status": "success",
                "status_code": result.get("status_code"),
            }
            if warning:
                attempt["warning"] = warning
            attempts.append(attempt)
            result["fallback_chain"] = list(attempts)
            result["fetch_policy"] = {
                "mode": mode,
                "order": order,
                "matched_domain": policy.get("matched_domain") or "",
            }
            if warning and index < len(order) - 1:
                last_warning_result = result
                continue
            if warning:
                result["fetch_warning"] = warning
            return result
        except Exception as exc:
            attempts.append(
                {
                    "engine": engine,
                    "status": "error",
                    "error_type": exc.__class__.__name__,
                    "error": str(exc)[:500],
                }
            )

    if last_warning_result:
        last_warning_result["fallback_chain"] = list(attempts)
        return last_warning_result

    raise FetchError(f"all fetch engines failed for {url}", attempts=attempts)
