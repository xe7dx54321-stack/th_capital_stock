#!/usr/bin/env python3
"""Helpers for public earnings-call transcript sources such as The Motley Fool."""

import html
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from smr_external_research import load_focus_equities
from smr_external_sources import html_snapshot, truncate_text
from smr_official_intel import DEFAULT_BROWSER_USER_AGENT, fetch_url
from smr_paths import project_path
from smr_universe import ordered_unique, parse_markdown_table
from smr_wiki import ensure_source_manifest_table

PUBLIC_TRANSCRIPT_TARGET_REGISTRY_PATH = project_path("00_control", "public_transcript_target_registry.md")
FOOL_LISTING_URL = "https://www.fool.com/earnings-call-transcripts/"

FOOL_LISTING_ENTRY_RE = re.compile(
    r'<a[^>]+href="(?P<href>/earnings/call-transcripts/[^"]+/)"[^>]*>.*?<h5[^>]*>(?P<title>[^<]+)</h5>',
    flags=re.I | re.S,
)
META_TAG_RE = re.compile(
    r'<meta[^>]+(?:name|property)="(?P<key>[^"]+)"[^>]+content="(?P<value>[^"]*)"[^>]*>',
    flags=re.I,
)
SCRIPT_RE = re.compile(r"<script\b.*?</script>", flags=re.I | re.S)
STYLE_RE = re.compile(r"<style\b.*?</style>", flags=re.I | re.S)
SPEAKER_RE = re.compile(r"(?:^|\n)([A-Z][A-Za-z .&'/-]{1,60}):")
QUARTER_RE = re.compile(r"\b(Q[1-4]\s+\d{4}|FY\s+\d{4}|H[12]\s+\d{4})\b", flags=re.I)
TITLE_SYMBOL_RE = re.compile(r"\((?P<symbol>[A-Z0-9.-]{1,12})\)")
COMPANY_TOKEN_RE = re.compile(r"[A-Z0-9]+")

COMPANY_STOPWORDS = {
    "ADR",
    "AND",
    "CLASS",
    "CO",
    "COMPANY",
    "CORP",
    "CORPORATION",
    "GROUP",
    "HOLDING",
    "HOLDINGS",
    "INC",
    "INCORPORATED",
    "LIMITED",
    "LTD",
    "PLC",
    "SA",
    "THE",
}

TRANSCRIPT_STOP_MARKERS = (
    "The Motley Fool has positions in",
    "Motley Fool Returns",
    "Premium Investing Services",
    "Stocks Mentioned",
    "View Premium Services",
    "Making the world smarter, happier, and richer.",
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


def normalize_csv_list(value):
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return ordered_unique(value.split(","))
    return ordered_unique(value)


def parse_public_transcript_target_registry(path_value=PUBLIC_TRANSCRIPT_TARGET_REGISTRY_PATH):
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
                "provider": str(row.get("Provider") or "").strip().lower() or "fool",
                "match_keywords": normalize_csv_list(row.get("Match Keywords")),
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


def extract_fool_listing_entries(html_text):
    entries = []
    seen = set()
    for match in FOOL_LISTING_ENTRY_RE.finditer(str(html_text or "")):
        href = urljoin(FOOL_LISTING_URL, html.unescape(match.group("href")))
        title = normalize_space(html.unescape(match.group("title")))
        if not href or not title or href in seen:
            continue
        seen.add(href)
        entries.append({"url": href, "title": title})
    return entries


def extract_title_symbol(title):
    match = TITLE_SYMBOL_RE.search(str(title or "").upper())
    if not match:
        return None
    return match.group("symbol")


def significant_company_tokens(text):
    tokens = []
    seen = set()
    for token in COMPANY_TOKEN_RE.findall(str(text or "").upper()):
        if len(token) <= 1 or token in COMPANY_STOPWORDS:
            continue
        if token in seen:
            continue
        seen.add(token)
        tokens.append(token)
    return tokens


def match_target_to_entry(target, entry):
    title = str(entry.get("title") or "")
    title_upper = title.upper()
    symbol = str(target.get("symbol") or "").strip().upper()
    entry_symbol = extract_title_symbol(title_upper)
    if symbol and entry_symbol:
        return entry_symbol == symbol
    if symbol and re.search(rf"(?<![A-Z0-9]){re.escape(symbol)}(?![A-Z0-9])", title_upper):
        return True
    for keyword in target.get("match_keywords") or []:
        keyword_upper = str(keyword or "").strip().upper()
        if not keyword_upper:
            continue
        if re.fullmatch(r"[A-Z0-9.-]{1,5}", keyword_upper):
            if re.search(rf"(?<![A-Z0-9]){re.escape(keyword_upper)}(?![A-Z0-9])", title_upper):
                return True
            continue
        if keyword_upper in title_upper:
            return True
    company_tokens = significant_company_tokens(target.get("company_name"))
    if company_tokens and all(token in title_upper for token in company_tokens[:2]):
        return True
    return False


def transcript_target_mismatch_reason(target, extracted):
    target_symbol = str(target.get("symbol") or "").strip().upper()
    extracted_symbol = str(extracted.get("symbol") or "").strip().upper()
    if target_symbol and extracted_symbol and target_symbol != extracted_symbol:
        return f"symbol_mismatch:{target_symbol}!={extracted_symbol}"
    target_tokens = set(significant_company_tokens(target.get("company_name")))
    extracted_tokens = set(
        significant_company_tokens(
            extracted.get("company_label") or extracted.get("title") or extracted.get("source_url")
        )
    )
    if target_tokens and extracted_tokens and not (target_tokens & extracted_tokens):
        return f"company_mismatch:{target.get('company_name')}!={extracted.get('company_label') or extracted.get('title')}"
    return None


def parse_meta_tags(html_text):
    meta = {}
    for match in META_TAG_RE.finditer(str(html_text or "")):
        key = str(match.group("key") or "").strip().lower()
        value = normalize_space(html.unescape(match.group("value")))
        if key and value and key not in meta:
            meta[key] = value
    return meta


def strip_scripts_and_styles(html_text):
    cleaned = SCRIPT_RE.sub("", str(html_text or ""))
    return STYLE_RE.sub("", cleaned)


def normalize_iso_timestamp(value):
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text.replace("T", " ").replace("Z", "")
    normalized = normalized.split("+", 1)[0].strip()
    if len(normalized) == 10:
        return f"{normalized} 00:00:00"
    return normalized[:19]


def extract_quarter_label(title):
    match = QUARTER_RE.search(str(title or ""))
    if not match:
        return None
    return match.group(1).upper()


def isolate_transcript_body(text):
    body = str(text or "")
    start = None
    for marker in ("Operator:", "Prepared Remarks:", "Call participants:"):
        idx = body.find(marker)
        if idx >= 0:
            start = idx
            break
    if start is not None:
        body = body[start:]
    for marker in TRANSCRIPT_STOP_MARKERS:
        idx = body.find(marker)
        if idx > 0:
            body = body[:idx]
            break
    return body.strip()


def extract_speakers(transcript_body, limit=10):
    speakers = []
    seen = set()
    for match in SPEAKER_RE.finditer(str(transcript_body or "")):
        name = normalize_space(match.group(1))
        if len(name) < 3 or len(name) > 50:
            continue
        if name in seen:
            continue
        seen.add(name)
        speakers.append(name)
        if len(speakers) >= limit:
            break
    return speakers


def transcript_summary(extracted):
    quarter_label = extracted.get("quarter_label")
    published_at = extracted.get("published_at")
    speaker_count = extracted.get("speaker_count") or 0
    speakers = extracted.get("speakers") or []
    parts = ["The Motley Fool 公开电话会文字稿已抓到"]
    if quarter_label:
        parts.append(f"覆盖 {quarter_label} 业绩会")
    if published_at:
        parts.append(f"发布时间 {published_at[:10]}")
    if speaker_count:
        parts.append(f"识别到约 {speaker_count} 位发言人")
    if speakers:
        parts.append(f"前几位包括 {', '.join(speakers[:3])}")
    parts.append("适合做管理层原话复核。")
    return "，".join(parts)


def extract_fool_transcript(response, target):
    html_text = response.get("text") or ""
    meta = parse_meta_tags(html_text)
    cleaned_html = strip_scripts_and_styles(html_text)
    title, page_text = html_snapshot(cleaned_html)
    transcript_body = isolate_transcript_body(page_text)
    speakers = extract_speakers(transcript_body)
    published_at = normalize_iso_timestamp(meta.get("article:published_time") or meta.get("date"))
    transcript_text = truncate_text(transcript_body, limit=24000)
    extracted = {
        "title": normalize_space(meta.get("title") or title or f"{target['company_name']} earnings call transcript"),
        "provider": "fool",
        "source_url": response.get("final_url"),
        "published_at": published_at,
        "article_author": meta.get("author"),
        "article_type": meta.get("article_type"),
        "collection": meta.get("collection"),
        "page_type": meta.get("page_type"),
        "quarter_label": extract_quarter_label(meta.get("title") or title),
        "symbol": (meta.get("primary_tickers") or meta.get("tickers") or target.get("symbol") or "").upper(),
        "company_label": meta.get("primary_tickers_companies") or target.get("company_name"),
        "speakers": speakers,
        "speaker_count": len(speakers),
        "transcript_word_count": len(re.findall(r"\b[\w'-]+\b", transcript_body)),
        "transcript_text": transcript_text,
    }
    extracted["summary"] = transcript_summary(extracted)
    return extracted


def parse_metadata_json(text):
    try:
        return json.loads(text or "{}")
    except json.JSONDecodeError:
        return {}


def load_json_rel_path(rel_path):
    if not rel_path:
        return None
    path = project_path(rel_path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def parse_date_prefix(value):
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def transcript_freshness_label(published_at):
    published_dt = parse_date_prefix(published_at)
    if published_dt is None:
        return "missing", None
    age_days = (datetime.now() - published_dt).days
    if age_days <= 7:
        return "fresh", age_days
    if age_days <= 35:
        return "usable", age_days
    return "stale", age_days


def enrich_transcript_snapshot(snapshot):
    if not snapshot:
        return None
    freshness_label, freshness_age_days = transcript_freshness_label(snapshot.get("published_at"))
    return {
        **snapshot,
        "freshness_label": freshness_label,
        "freshness_age_days": freshness_age_days,
        "summary": snapshot.get("summary") or transcript_summary(snapshot),
    }


def latest_public_transcript_snapshot(conn, ts_code):
    ensure_source_manifest_table(conn)
    rows = conn.execute(
        """
        SELECT title, source_rel_path, metadata_json, updated_at
        FROM source_manifest
        WHERE status='active'
          AND source_type='external_source_snapshot'
          AND entity_id=?
          AND json_extract(metadata_json, '$.source_kind')='public_transcript'
        ORDER BY datetime(updated_at) DESC, source_id DESC
        LIMIT 4
        """,
        (ts_code,),
    ).fetchall()

    for title, source_rel_path, metadata_json, updated_at in rows:
        metadata = parse_metadata_json(metadata_json)
        meta_payload = load_json_rel_path(metadata.get("meta_rel_path"))
        if not meta_payload:
            continue
        return enrich_transcript_snapshot(
            {
                "source_kind": "public_transcript",
                "provider": meta_payload.get("provider") or "fool",
                "title": title,
                "source_rel_path": source_rel_path,
                "updated_at": updated_at,
                "published_at": meta_payload.get("published_at"),
                "article_author": meta_payload.get("article_author"),
                "article_type": meta_payload.get("article_type"),
                "quarter_label": meta_payload.get("quarter_label"),
                "symbol": meta_payload.get("symbol"),
                "company_label": meta_payload.get("company_label"),
                "speaker_count": meta_payload.get("speaker_count"),
                "speakers": meta_payload.get("speakers") or [],
                "transcript_word_count": meta_payload.get("transcript_word_count"),
                "summary": meta_payload.get("summary"),
            }
        )
    return None


def load_public_transcript_digest(conn, limit=7, focus_ts_codes=None, fallback_to_pool=True):
    def registry_target_rows():
        rows = []
        seen = set()
        for row in parse_public_transcript_target_registry():
            if not row.get("enabled"):
                continue
            if row.get("provider") != "fool":
                continue
            ts_code = row.get("entity_id")
            if not ts_code or ts_code in seen:
                continue
            seen.add(ts_code)
            rows.append(row)
        return rows

    def registry_target_ts_codes():
        codes = []
        for row in registry_rows:
            ts_code = row.get("entity_id")
            codes.append(ts_code)
        return codes

    def append_focus_items(focus_items, items, seen_codes):
        for focus in focus_items:
            ts_code = focus.get("ts_code")
            if not ts_code or ts_code in seen_codes:
                continue
            snapshot = latest_public_transcript_snapshot(conn, ts_code)
            if not snapshot:
                continue
            row = registry_rows_by_code.get(ts_code) or {}
            items.append(
                {
                    "ts_code": ts_code,
                    "name": focus.get("name") or row.get("company_name") or ts_code,
                    "sector": focus.get("sector") or row.get("market") or "US",
                    "pool_types": focus.get("pool_types") or [f"public_transcript/{row.get('status') or 'live'}"],
                    "score": focus.get("score", 0),
                    **snapshot,
                }
            )
            seen_codes.add(ts_code)
            if len(items) >= limit:
                break

    def append_registry_fallback_items(ts_codes, items, seen_codes):
        for ts_code in ts_codes:
            if not ts_code or ts_code in seen_codes:
                continue
            snapshot = latest_public_transcript_snapshot(conn, ts_code)
            if not snapshot:
                continue
            row = registry_rows_by_code.get(ts_code) or {}
            items.append(
                {
                    "ts_code": ts_code,
                    "name": row.get("company_name") or ts_code,
                    "sector": row.get("market") or "US",
                    "pool_types": [f"public_transcript/{row.get('status') or 'live'}"],
                    "score": 0,
                    **snapshot,
                }
            )
            seen_codes.add(ts_code)
            if len(items) >= limit:
                break

    registry_rows = registry_target_rows()
    registry_rows_by_code = {row.get("entity_id"): row for row in registry_rows if row.get("entity_id")}
    requested_codes = [ts_code for ts_code in (focus_ts_codes or []) if ts_code]
    if requested_codes:
        focus_strategy = "explicit_ts_codes"
        focus_items = load_focus_equities(
            conn,
            limit=max(limit, len(requested_codes)),
            focus_ts_codes=requested_codes,
        )
    elif fallback_to_pool:
        focus_strategy = "top_pool"
        focus_items = load_focus_equities(conn, limit=limit)
    else:
        focus_strategy = "none"
        focus_items = []

    items = []
    seen_codes = set()
    append_focus_items(focus_items[:limit], items, seen_codes)
    append_registry_fallback_items(requested_codes or registry_target_ts_codes(), items, seen_codes)

    if len(items) < limit and not requested_codes:
        fallback_codes = [code for code in registry_target_ts_codes() if code not in seen_codes]
        if fallback_codes:
            focus_strategy = "pool_plus_registry_targets" if focus_strategy == "top_pool" else "registry_targets"
            fallback_focus_items = load_focus_equities(
                conn,
                limit=max(limit, len(fallback_codes)),
                focus_ts_codes=fallback_codes,
            )
            append_focus_items(fallback_focus_items, items, seen_codes)
            append_registry_fallback_items(fallback_codes, items, seen_codes)

    return {
        "focus_strategy": focus_strategy,
        "requested_focus_count": len(requested_codes),
        "focus_count": len(items),
        "focus_ts_codes": requested_codes[:limit],
        "items": items,
    }
