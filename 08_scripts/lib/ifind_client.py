#!/usr/bin/env python3
"""Small iFinD QuantAPI HTTP client.

Authentication order:
1. Use IFIND_ACCESS_TOKEN if present.
2. Otherwise use cached token generated from IFIND_REFRESH_TOKEN.
3. Otherwise call /get_access_token with IFIND_REFRESH_TOKEN.

No third-party packages are required.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://quantapi.51ifind.com/api/v1"
DEFAULT_CACHE_PATH = Path(".ifind") / "token_cache.json"
DEFAULT_CACHE_TTL_SECONDS = 6 * 24 * 60 * 60


class IFindError(RuntimeError):
    """Raised for iFinD client setup or HTTP errors."""


def mask_token(token: str) -> str:
    if not token:
        return ""
    if len(token) <= 12:
        return token[:2] + "***" + token[-2:]
    return token[:8] + "..." + token[-6:]


class IFindClient:
    def __init__(
        self,
        base_url: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        cache_path: str | os.PathLike[str] | None = None,
        timeout: int = 60,
        use_env_proxy: bool | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("IFIND_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.env_access_token = access_token or os.getenv("IFIND_ACCESS_TOKEN") or ""
        self.refresh_token = refresh_token or os.getenv("IFIND_REFRESH_TOKEN") or ""
        self.cache_path = Path(cache_path or os.getenv("IFIND_TOKEN_CACHE") or DEFAULT_CACHE_PATH)
        self.timeout = timeout
        if use_env_proxy is None:
            disable_proxy = (os.getenv("IFIND_DISABLE_PROXY") or "").strip().lower()
            use_env_proxy = disable_proxy not in {"1", "true", "yes", "on"}
        self.use_env_proxy = use_env_proxy

    def _post_json(self, endpoint: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        url = endpoint if endpoint.startswith("http") else f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = {"Content-Type": "application/json", **headers}
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=request_headers, method="POST")

        opener = urllib.request.build_opener()
        if not self.use_env_proxy:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        try:
            with opener.open(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise IFindError(f"HTTP {exc.code} from {url}: {body[:1000]}") from exc
        except urllib.error.URLError as exc:
            raise IFindError(f"Network error calling {url}: {exc}") from exc

        try:
            result = json.loads(body)
        except json.JSONDecodeError as exc:
            raise IFindError(f"Non-JSON response from {url}: {body[:1000]}") from exc

        return result

    def _read_cached_access_token(self) -> str:
        if not self.cache_path.exists():
            return ""
        try:
            cache = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ""

        token = str(cache.get("access_token") or "")
        expires_at = float(cache.get("expires_at") or 0)
        if token and expires_at > time.time():
            return token
        return ""

    def _write_cached_access_token(self, token: str) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache = {
            "access_token": token,
            "created_at": int(time.time()),
            "expires_at": int(time.time() + DEFAULT_CACHE_TTL_SECONDS),
        }
        self.cache_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")

    def get_access_token(self, force_refresh: bool = False) -> str:
        if self.env_access_token and not force_refresh:
            return self.env_access_token

        if not force_refresh:
            cached = self._read_cached_access_token()
            if cached:
                return cached

        if not self.refresh_token:
            raise IFindError("Set IFIND_REFRESH_TOKEN or IFIND_ACCESS_TOKEN first.")

        response = self._post_json(
            "get_access_token",
            {},
            {"refresh_token": self.refresh_token},
        )
        token = str((response.get("data") or {}).get("access_token") or "")
        if not token:
            raise IFindError(f"Could not obtain access_token: {json.dumps(response, ensure_ascii=False)[:1000]}")

        self._write_cached_access_token(token)
        return token

    def call(self, endpoint: str, payload: dict[str, Any], force_refresh: bool = False) -> dict[str, Any]:
        access_token = self.get_access_token(force_refresh=force_refresh)
        return self._post_json(
            endpoint,
            payload,
            {
                "access_token": access_token,
                "ifindlang": "cn",
            },
        )


def load_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.payload_file:
        return json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
    if args.payload_json:
        return json.loads(args.payload_json)
    raise IFindError("Provide --payload-json or --payload-file.")


def print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_token(args: argparse.Namespace) -> int:
    client = IFindClient(cache_path=args.cache, use_env_proxy=not args.no_proxy)
    token = client.get_access_token(force_refresh=args.force_refresh)
    source = "IFIND_ACCESS_TOKEN" if client.env_access_token and not args.force_refresh else "refresh/cache"
    print(f"access_token={mask_token(token)}")
    print(f"source={source}")
    print(f"cache={client.cache_path}")
    return 0


def cmd_smoke(args: argparse.Namespace) -> int:
    client = IFindClient(cache_path=args.cache, timeout=args.timeout, use_env_proxy=not args.no_proxy)
    payload = {
        "codes": "300033.SZ",
        "indipara": [
            {
                "indicator": "ths_stock_short_name_stock",
                "indiparams": [],
            }
        ],
    }
    result = client.call("basic_data_service", payload, force_refresh=args.force_refresh)
    print_json(result)
    return 0


def cmd_quote_smoke(args: argparse.Namespace) -> int:
    client = IFindClient(cache_path=args.cache, timeout=args.timeout, use_env_proxy=not args.no_proxy)
    payload = {
        "codes": "300033.SZ,000001.SZ",
        "indipara": [
            {"indicator": "ths_close_price_stock", "indiparams": [args.date, "100", args.date]},
            {"indicator": "ths_pb_mrq_stock", "indiparams": [args.date]},
            {"indicator": "ths_turnover_ratio_stock", "indiparams": [args.date]},
        ],
    }
    result = client.call("basic_data_service", payload, force_refresh=args.force_refresh)
    print_json(result)
    return 0


def cmd_date_sequence_smoke(args: argparse.Namespace) -> int:
    client = IFindClient(cache_path=args.cache, timeout=args.timeout, use_env_proxy=not args.no_proxy)
    payload = {
        "codes": "300033.SZ,000001.SZ",
        "startdate": args.startdate,
        "enddate": args.enddate,
        "functionpara": {"Fill": "Blank"},
        "indipara": [
            {"indicator": "ths_close_price_stock", "indiparams": ["", "100", ""]},
            {"indicator": "ths_pb_mrq_stock", "indiparams": [""]},
            {"indicator": "ths_turnover_ratio_stock", "indiparams": [""]},
        ],
    }
    result = client.call("date_sequence", payload, force_refresh=args.force_refresh)
    print_json(result)
    return 0


def cmd_call(args: argparse.Namespace) -> int:
    client = IFindClient(cache_path=args.cache, timeout=args.timeout, use_env_proxy=not args.no_proxy)
    payload = load_payload(args)
    result = client.call(args.endpoint, payload, force_refresh=args.force_refresh)
    print_json(result)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="iFinD QuantAPI HTTP client")
    parser.add_argument("--cache", default=str(DEFAULT_CACHE_PATH), help="access token cache path")
    parser.add_argument("--timeout", type=int, default=60, help="HTTP timeout seconds")
    parser.add_argument("--force-refresh", action="store_true", help="refresh access_token before calling")
    parser.add_argument("--no-proxy", action="store_true", help="ignore HTTP_PROXY/HTTPS_PROXY environment variables")

    subparsers = parser.add_subparsers(dest="command", required=True)

    token_parser = subparsers.add_parser("token", help="obtain and mask access_token")
    token_parser.set_defaults(func=cmd_token)

    smoke_parser = subparsers.add_parser("smoke", help="run a small basic_data_service request")
    smoke_parser.set_defaults(func=cmd_smoke)

    quote_parser = subparsers.add_parser("quote-smoke", help="run a small market-data request")
    quote_parser.add_argument("--date", default="20250401", help="trade date in YYYYMMDD")
    quote_parser.set_defaults(func=cmd_quote_smoke)

    seq_parser = subparsers.add_parser("date-sequence-smoke", help="run a small historical quote request")
    seq_parser.add_argument("--startdate", default="20250401", help="start date in YYYYMMDD")
    seq_parser.add_argument("--enddate", default="20250403", help="end date in YYYYMMDD")
    seq_parser.set_defaults(func=cmd_date_sequence_smoke)

    call_parser = subparsers.add_parser("call", help="call any iFinD endpoint with JSON payload")
    call_parser.add_argument("endpoint", help="endpoint name, e.g. basic_data_service")
    call_parser.add_argument("--payload-json", help="JSON payload string")
    call_parser.add_argument("--payload-file", help="path to JSON payload file")
    call_parser.set_defaults(func=cmd_call)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except IFindError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON payload: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
