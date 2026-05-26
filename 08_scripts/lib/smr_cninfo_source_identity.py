#!/usr/bin/env python3
"""Resolve CNINFO source identity hints for financial statement discovery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from smr_paths import project_path


MANIFEST_PATH = project_path("00_control", "financial_statement_sources.json")

CURATED_CNINFO_IDENTITIES: dict[str, dict[str, Any]] = {
    "300308.SZ": {
        "org_id": "9900022016",
        "exchange": "SZSE",
        "security_code": "300308",
        "security_name": "中际旭创",
        "plate": "sz",
        "column": "szse",
        "identity_source": "curated_manifest",
        "confidence": 0.9,
    },
    "688041.SH": {
        "org_id": "9900048365",
        "exchange": "SSE",
        "security_code": "688041",
        "security_name": "海光信息",
        "plate": "sh",
        "column": "sse",
        "identity_source": "curated_manifest",
        "confidence": 0.9,
    },
}


def _load_manifest(path: Path | None = None) -> dict[str, Any]:
    manifest_path = path or MANIFEST_PATH
    if not manifest_path.exists():
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _market_for_ticker(ticker: str) -> str:
    value = ticker.upper()
    if value.endswith(".HK"):
        return "HK"
    if value.endswith((".SZ", ".SH", ".BJ")):
        return "CN"
    return "US"


def _identity_from_manifest(ticker: str, manifest: dict[str, Any]) -> dict[str, Any] | None:
    identities = manifest.get("source_identities") or {}
    identity = identities.get(ticker)
    if isinstance(identity, dict) and identity.get("org_id"):
        return {**identity, "identity_source": identity.get("identity_source") or "manifest", "confidence": float(identity.get("confidence") or 0.82)}
    for source in (manifest.get("sources") or {}).get(ticker, []):
        identity = source.get("source_identity") or {}
        if isinstance(identity, dict) and identity.get("org_id"):
            return {**identity, "identity_source": identity.get("identity_source") or "manifest_source", "confidence": float(identity.get("confidence") or 0.78)}
    return None


def resolve_cninfo_source_identity(ticker: str, *, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    ticker = ticker.upper()
    if _market_for_ticker(ticker) != "CN":
        return {
            "ticker": ticker,
            "market": _market_for_ticker(ticker),
            "status": "unsupported_market",
            "missing_reason": "cninfo_identity_only_for_cn_tickers",
        }
    manifest = manifest if manifest is not None else _load_manifest()
    identity = _identity_from_manifest(ticker, manifest) or CURATED_CNINFO_IDENTITIES.get(ticker)
    if not identity:
        return {
            "ticker": ticker,
            "market": "CN",
            "status": "unresolved",
            "missing_reason": "cninfo_org_id_missing",
            "suggested_fix": f"add CNINFO org_id/source manifest entry for {ticker}",
        }
    org_id = str(identity.get("org_id") or "").strip()
    plate = str(identity.get("plate") or ("sh" if ticker.endswith(".SH") else "sz")).strip()
    column = str(identity.get("column") or ("sse" if ticker.endswith(".SH") else "szse")).strip()
    security_code = str(identity.get("security_code") or ticker.split(".")[0]).strip()
    exchange = str(identity.get("exchange") or ("SSE" if ticker.endswith(".SH") else "SZSE")).strip()
    return {
        "ticker": ticker,
        "market": "CN",
        "status": "resolved",
        "org_id": org_id,
        "exchange": exchange,
        "security_code": security_code,
        "security_name": identity.get("security_name"),
        "plate": plate,
        "column": column,
        "identity_source": identity.get("identity_source") or "manifest_or_inferred",
        "confidence": float(identity.get("confidence") or 0.78),
        "query_hint": {"org_id": org_id, "plate": plate, "column": column},
    }


def cninfo_query_hint(ticker: str) -> dict[str, str] | None:
    identity = resolve_cninfo_source_identity(ticker)
    if identity.get("status") != "resolved":
        return None
    hint = identity.get("query_hint") or {}
    return {"org_id": str(hint.get("org_id")), "plate": str(hint.get("plate")), "column": str(hint.get("column"))}
