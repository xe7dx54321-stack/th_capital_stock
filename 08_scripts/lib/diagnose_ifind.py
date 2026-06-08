#!/usr/bin/env python3
"""Diagnose iFinD QuantAPI setup on a new computer.

The output intentionally masks tokens. Share the full output when asking for
help; it should not reveal secrets.
"""

from __future__ import annotations

import json
import os
import platform
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from ifind_client import DEFAULT_BASE_URL, IFindClient, IFindError, mask_token


HOST = "quantapi.51ifind.com"
PORT = 443


def status(name: str, ok: bool, detail: str = "") -> bool:
    mark = "OK" if ok else "FAIL"
    line = f"[{mark}] {name}"
    if detail:
        line += f": {detail}"
    print(line)
    return ok


def summarize_response(result: dict[str, Any]) -> str:
    errorcode = result.get("errorcode")
    errmsg = result.get("errmsg") or result.get("message") or ""
    tables = result.get("tables")
    data = result.get("data")
    parts = [f"errorcode={errorcode!r}"]
    if errmsg:
        parts.append(f"errmsg={errmsg}")
    if isinstance(tables, list):
        parts.append(f"tables={len(tables)}")
    if isinstance(data, (list, dict)):
        parts.append(f"data_type={type(data).__name__}")
    return ", ".join(parts)


def print_sample(result: dict[str, Any]) -> None:
    text = json.dumps(result, ensure_ascii=False)
    print("sample=" + text[:800])


def check_dns() -> bool:
    try:
        infos = socket.getaddrinfo(HOST, PORT, proto=socket.IPPROTO_TCP)
    except OSError as exc:
        return status("DNS", False, str(exc))

    addrs = sorted({item[4][0] for item in infos})
    return status("DNS", True, ", ".join(addrs[:5]))


def check_tls() -> bool:
    try:
        with socket.create_connection((HOST, PORT), timeout=10) as sock:
            context = ssl.create_default_context()
            with context.wrap_socket(sock, server_hostname=HOST) as tls_sock:
                cert = tls_sock.getpeercert()
    except OSError as exc:
        return status("TLS direct connection", False, str(exc))
    except ssl.SSLError as exc:
        return status("TLS direct connection", False, str(exc))

    subject = cert.get("subject", [])
    cn = ""
    for group in subject:
        for key, value in group:
            if key == "commonName":
                cn = value
                break
    return status("TLS direct connection", True, cn or "certificate received")


def check_http(client: IFindClient, label: str) -> bool:
    req = urllib.request.Request(client.base_url, method="GET")
    opener = urllib.request.build_opener()
    if not client.use_env_proxy:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=10) as resp:
            detail = f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        detail = f"HTTP {exc.code} reachable"
    except urllib.error.URLError as exc:
        return status(label, False, str(exc))
    return status(label, True, detail)


def run_api_check(name: str, fn) -> bool:
    started = time.time()
    try:
        result = fn()
    except IFindError as exc:
        return status(name, False, str(exc))
    except Exception as exc:
        return status(name, False, f"{type(exc).__name__}: {exc}")

    elapsed = time.time() - started
    ok = result.get("errorcode") in (0, "0", None)
    status(name, ok, summarize_response(result) + f", elapsed={elapsed:.1f}s")
    print_sample(result)
    return ok


def main() -> int:
    print("== iFinD QuantAPI diagnostics ==")
    print(f"python={sys.version.split()[0]} ({platform.system()} {platform.release()})")
    print(f"cwd={Path.cwd()}")
    print(f"base_url={os.getenv('IFIND_BASE_URL') or DEFAULT_BASE_URL}")

    access_token = os.getenv("IFIND_ACCESS_TOKEN") or ""
    refresh_token = os.getenv("IFIND_REFRESH_TOKEN") or ""
    https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy") or ""
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy") or ""

    status("IFIND_ACCESS_TOKEN", bool(access_token), mask_token(access_token) if access_token else "not set")
    status("IFIND_REFRESH_TOKEN", bool(refresh_token), mask_token(refresh_token) if refresh_token else "not set")
    status("HTTPS_PROXY", bool(https_proxy), "set" if https_proxy else "not set")
    status("HTTP_PROXY", bool(http_proxy), "set" if http_proxy else "not set")
    disable_proxy = (os.getenv("IFIND_DISABLE_PROXY") or "").strip().lower()
    status("IFIND_DISABLE_PROXY", bool(disable_proxy), disable_proxy or "not set")

    client = IFindClient(timeout=60)
    direct_client = IFindClient(timeout=60, use_env_proxy=False)
    print(f"cache_path={client.cache_path}")

    client_http_label = (
        "HTTP reachability with proxy disabled"
        if not client.use_env_proxy
        else "HTTP reachability with environment proxy"
    )
    checks = [
        check_dns(),
        check_tls(),
    ]

    client_http_ok = check_http(client, client_http_label)
    checks.append(client_http_ok)
    direct_http_ok = check_http(direct_client, "HTTP reachability without proxy")
    checks.append(direct_http_ok)

    if client.use_env_proxy and not client_http_ok and direct_http_ok:
        print("proxy_hint=Environment proxy failed, but direct connection works. Try IFIND_DISABLE_PROXY=1 or --no-proxy.")

    try:
        token = client.get_access_token()
    except Exception as exc:
        checks.append(status("access token", False, f"{type(exc).__name__}: {exc}"))
        print("\nNext step: run .\\set_ifind_env.ps1 -Persist and reopen Codex/PowerShell.")
        return 1

    checks.append(status("access token", True, mask_token(token)))

    checks.append(
        run_api_check(
            "basic_data_service name smoke",
            lambda: client.call(
                "basic_data_service",
                {
                    "codes": "300033.SZ",
                    "indipara": [
                        {"indicator": "ths_stock_short_name_stock", "indiparams": []}
                    ],
                },
            ),
        )
    )

    checks.append(
        run_api_check(
            "basic_data_service quote smoke",
            lambda: client.call(
                "basic_data_service",
                {
                    "codes": "300033.SZ,000001.SZ",
                    "indipara": [
                        {"indicator": "ths_close_price_stock", "indiparams": ["20250401", "100", "20250401"]},
                        {"indicator": "ths_pb_mrq_stock", "indiparams": ["20250401"]},
                        {"indicator": "ths_turnover_ratio_stock", "indiparams": ["20250401"]},
                    ],
                },
            ),
        )
    )

    checks.append(
        run_api_check(
            "date_sequence quote smoke",
            lambda: client.call(
                "date_sequence",
                {
                    "codes": "300033.SZ,000001.SZ",
                    "startdate": "20250401",
                    "enddate": "20250403",
                    "functionpara": {"Fill": "Blank"},
                    "indipara": [
                        {"indicator": "ths_close_price_stock", "indiparams": ["", "100", ""]},
                        {"indicator": "ths_pb_mrq_stock", "indiparams": [""]},
                        {"indicator": "ths_turnover_ratio_stock", "indiparams": [""]},
                    ],
                },
            ),
        )
    )

    print("\n== diagnosis ==")
    if all(checks):
        print("All checks passed. The API and market-data indicators are usable from this machine.")
        return 0

    print("Some checks failed. Use TROUBLESHOOTING.md to match the first failing line.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
