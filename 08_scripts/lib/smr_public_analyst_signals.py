#!/usr/bin/env python3
"""Helpers for public analyst-signal sources such as MarketScreener consensus pages."""

import html
import re
from pathlib import Path

from smr_official_intel import (
    DEFAULT_BROWSER_USER_AGENT,
    fetch_url,
    response_domain,
    response_extension,
)
from smr_paths import project_path
from smr_universe import ordered_unique, parse_markdown_table

PUBLIC_ANALYST_SIGNAL_TARGET_REGISTRY_PATH = project_path("00_control", "public_analyst_signal_target_registry.md")

REQUIRED_LABELS = (
    "Mean consensus",
    "Number of Analysts",
    "Last Close Price",
    "Average target price",
    "Spread / Average Target",
    "High Price Target",
    "Spread / Highest target",
    "Low Price Target",
    "Spread / Lowest Target",
)


def section_lines(path_value):
    path = Path(path_value)
    if not path.exists():
        return {}
    sections = {}
    current = None
    buffer = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = buffer
            current = line[3:].strip()
            buffer = []
            continue
        if current is not None:
            buffer.append(line)
    if current is not None:
        sections[current] = buffer
    return sections


def parse_bool(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "enabled", "active"}


def normalize_space(text):
    return " ".join(str(text or "").split())


def strip_html(raw_text):
    cleaned = re.sub(r"<[^>]+>", " ", str(raw_text or ""))
    return normalize_space(html.unescape(cleaned))


def parse_public_analyst_signal_target_registry(path_value=PUBLIC_ANALYST_SIGNAL_TARGET_REGISTRY_PATH):
    sections = section_lines(path_value)
    rows = []
    for row in parse_markdown_table(sections.get("Targets", [])):
        target_key = str(row.get("Target Key") or "").strip()
        if not target_key:
            continue
        rows.append(
            {
                "target_key": target_key,
                "entity_type": str(row.get("Entity Type") or "").strip() or "stock",
                "entity_id": str(row.get("Entity ID") or "").strip(),
                "company_name": str(row.get("Company") or "").strip(),
                "market": str(row.get("Market") or "").strip().upper(),
                "symbol": str(row.get("Symbol") or "").strip().upper(),
                "provider": str(row.get("Provider") or "").strip().lower() or "marketscreener",
                "consensus_url": str(row.get("Consensus URL") or "").strip(),
                "status": str(row.get("Status") or "").strip() or "planned",
                "enabled": parse_bool(row.get("Enabled")),
                "notes": str(row.get("Notes") or "").strip(),
            }
        )
    return rows


def select_target_rows(target_rows, target_keys=None, entity_ids=None, enabled_only=True):
    key_filter = {str(item or "").strip() for item in (target_keys or []) if str(item or "").strip()}
    entity_filter = {str(item or "").strip() for item in (entity_ids or []) if str(item or "").strip()}
    rows = []
    for row in target_rows:
        if enabled_only and not row.get("enabled"):
            continue
        if key_filter and row["target_key"] not in key_filter:
            continue
        if entity_filter and row["entity_id"] not in entity_filter:
            continue
        rows.append(row)
    return rows


def extract_title(html_text):
    match = re.search(r"<title>(.*?)</title>", str(html_text or ""), flags=re.I | re.S)
    if not match:
        return ""
    return normalize_space(html.unescape(match.group(1)))


def extract_symbol_from_title(page_title):
    match = re.search(r"\|\s*([A-Z0-9.\-]+)\s*\|", str(page_title or ""))
    if match:
        return match.group(1).strip().upper()
    return ""


def extract_label_values(html_text):
    rows = {}
    pattern = re.compile(
        r'<div class="c">\s*([^<]+?)\s*</div>\s*<div class="c-auto[^>]*txt-bold[^>]*">(.*?)</div>',
        flags=re.I | re.S,
    )
    for match in pattern.finditer(str(html_text or "")):
        label = strip_html(match.group(1))
        value = strip_html(match.group(2))
        if not label or not value or label in rows:
            continue
        rows[label] = value
    return rows


def parse_float(value):
    match = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", str(value or ""))
    if not match:
        return None
    try:
        return float(match.group(0).replace(",", ""))
    except ValueError:
        return None


def parse_int(value):
    match = re.search(r"\d[\d,]*", str(value or ""))
    if not match:
        return None
    try:
        return int(match.group(0).replace(",", ""))
    except ValueError:
        return None


def parse_percent(value):
    return parse_float(value)


def parse_price_and_currency(value):
    text = normalize_space(value)
    price = parse_float(text)
    currency_match = re.search(r"([A-Z]{2,5})$", text)
    return {
        "raw": text,
        "value": price,
        "currency": currency_match.group(1) if currency_match else None,
    }


def validate_required_fields(label_values, target, page_title):
    missing = [label for label in REQUIRED_LABELS if not label_values.get(label)]
    if missing:
        raise ValueError(
            "required consensus fields missing: "
            + ", ".join(missing[:4])
            + (f" | page_title={page_title}" if page_title else "")
        )
    expected_symbol = str(target.get("symbol") or target.get("entity_id") or "").strip().upper()
    actual_symbol = extract_symbol_from_title(page_title)
    if expected_symbol and actual_symbol and expected_symbol != actual_symbol:
        raise ValueError(f"target mismatch: expected {expected_symbol}, got {actual_symbol}")


def extract_marketscreener_consensus(response, target):
    html_text = response.get("text") or ""
    page_title = extract_title(html_text)
    label_values = extract_label_values(html_text)
    validate_required_fields(label_values, target, page_title)

    last_close = parse_price_and_currency(label_values["Last Close Price"])
    average_target = parse_price_and_currency(label_values["Average target price"])
    high_target = parse_price_and_currency(label_values["High Price Target"])
    low_target = parse_price_and_currency(label_values["Low Price Target"])

    return {
        "title": page_title or f"{target['company_name']} MarketScreener consensus",
        "page_title": page_title,
        "provider": "marketscreener",
        "consensus_url": response.get("final_url") or target.get("consensus_url"),
        "mean_consensus": label_values["Mean consensus"],
        "analysts_count": parse_int(label_values["Number of Analysts"]),
        "last_close_price": last_close["value"],
        "last_close_currency": last_close["currency"],
        "last_close_raw": last_close["raw"],
        "average_target_price": average_target["value"],
        "average_target_currency": average_target["currency"],
        "average_target_raw": average_target["raw"],
        "spread_avg_target_pct": parse_percent(label_values["Spread / Average Target"]),
        "high_target_price": high_target["value"],
        "high_target_currency": high_target["currency"],
        "high_target_raw": high_target["raw"],
        "spread_high_target_pct": parse_percent(label_values["Spread / Highest target"]),
        "low_target_price": low_target["value"],
        "low_target_currency": low_target["currency"],
        "low_target_raw": low_target["raw"],
        "spread_low_target_pct": parse_percent(label_values["Spread / Lowest Target"]),
        "raw_label_values": {label: label_values[label] for label in ordered_unique(REQUIRED_LABELS)},
    }
