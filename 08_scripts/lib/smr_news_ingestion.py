#!/usr/bin/env python3
"""News ingestion, dedupe, freshness, and evidence export for SMR."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any

from smr_claim_graph import ensure_claim_graph_tables, upsert_evidence
from smr_paths import normalize_project_path, relative_to_project
from smr_wiki import generate_execution_id, loads_json, now_ts, read_markdown

NEWS_SOURCE_KEYS = {
    "eastmoney_news_article",
    "eastmoney_news_search",
    "manual_news",
    "news_article",
    "news_search",
    "public_analyst_signal_marketscreener",
    "yahoo_finance_rss",
}


def ensure_news_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS news_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id TEXT UNIQUE NOT NULL,
            source_key TEXT,
            source_name TEXT,
            title TEXT NOT NULL,
            body TEXT,
            url TEXT,
            published_at TEXT,
            ingested_at TEXT NOT NULL,
            tickers_json TEXT NOT NULL DEFAULT '[]',
            themes_json TEXT NOT NULL DEFAULT '[]',
            entities_json TEXT NOT NULL DEFAULT '[]',
            language TEXT,
            market TEXT,
            credibility TEXT,
            dedupe_hash TEXT NOT NULL,
            title_fingerprint TEXT,
            source_list_json TEXT NOT NULL DEFAULT '[]',
            metadata_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_news_items_dedupe_hash
        ON news_items(dedupe_hash);

        CREATE UNIQUE INDEX IF NOT EXISTS idx_news_items_url
        ON news_items(url)
        WHERE url IS NOT NULL AND url != '';

        CREATE INDEX IF NOT EXISTS idx_news_items_title_fingerprint
        ON news_items(title_fingerprint, published_at DESC);

        CREATE INDEX IF NOT EXISTS idx_news_items_source_market
        ON news_items(source_key, market, published_at DESC);
        """
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(news_items)").fetchall()}
    if "title_fingerprint" not in columns:
        conn.execute("ALTER TABLE news_items ADD COLUMN title_fingerprint TEXT")


def relation_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?",
        (name,),
    ).fetchone()
    return bool(row)


def table_columns(conn: sqlite3.Connection, name: str) -> set[str]:
    if not relation_exists(conn, name):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({name})").fetchall()}


def parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    text = text.replace("T", " ")[:19]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[: len(fmt)], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def normalize_dt(value: Any) -> str | None:
    dt_value = parse_dt(value)
    if not dt_value:
        return None
    return dt_value.strftime("%Y-%m-%d %H:%M:%S")


def normalize_text(value: Any, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit is not None and len(text) > limit:
        return text[:limit].rstrip()
    return text


def stable_hash(*parts: Any) -> str:
    raw = "|".join(normalize_text(part).lower() for part in parts if part not in (None, ""))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def canonical_news_url(url: Any) -> str:
    text = normalize_text(url, limit=1200)
    if not text:
        return ""
    parsed = urllib.parse.urlsplit(text)
    if not parsed.scheme and not parsed.netloc:
        return text
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    query_items = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    filtered_query = [
        (key, value)
        for key, value in query_items
        if not key.lower().startswith("utm_")
        and key.lower() not in {"spm", "ref", "from", "source", "cfrom", "cmpid", "share"}
    ]
    query = urllib.parse.urlencode(filtered_query, doseq=True)
    return urllib.parse.urlunsplit((scheme, netloc, path or "/", query, ""))


def title_fingerprint(title: str) -> str:
    compact = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", normalize_text(title).lower())
    return stable_hash(compact[:160])


def infer_market(tickers: list[str], fallback: str | None = None) -> str:
    fallback_text = str(fallback or "").strip().upper()
    if fallback_text in {"A", "H", "HK", "US", "GLOBAL"}:
        return "H" if fallback_text == "HK" else fallback_text
    for ticker in tickers:
        text = str(ticker or "").upper()
        if text.endswith((".SZ", ".SH", ".BJ")):
            return "A"
        if text.endswith(".HK"):
            return "H"
        if text:
            return "US"
    return "global"


def infer_tickers(*values: Any) -> list[str]:
    text = " ".join(str(value or "") for value in values)
    matches = re.findall(r"([0-9]{6}\.(?:SZ|SH|BJ)|[0-9]{5}\.HK|[A-Z]{1,6})", text)
    result = []
    seen = set()
    for ticker in matches:
        if ticker in seen:
            continue
        seen.add(ticker)
        result.append(ticker)
    return result


def yahoo_symbol_for_ticker(ticker: str) -> str:
    text = str(ticker or "").strip().upper()
    if re.match(r"^[0-9]{5}\.HK$", text):
        return f"{int(text.split('.')[0])}.HK"
    return text


def fetch_yahoo_finance_news(ticker: str, limit: int = 20, timeout: int = 30) -> list[dict[str, Any]]:
    symbol = yahoo_symbol_for_ticker(ticker)
    params = urllib.parse.urlencode({"s": symbol, "region": "US", "lang": "en-US"})
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?{params}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8", errors="replace")
    root = ET.fromstring(payload)
    items = []
    for item in root.findall(".//item")[:limit]:
        title = normalize_text(item.findtext("title"), limit=500)
        link = normalize_text(item.findtext("link"), limit=1200)
        description = normalize_text(item.findtext("description"), limit=12000)
        pub_date = item.findtext("pubDate")
        published_at = None
        if pub_date:
            try:
                published_at = parsedate_to_datetime(pub_date).strftime("%Y-%m-%d %H:%M:%S")
            except (TypeError, ValueError, AttributeError):
                published_at = None
        if not title:
            continue
        items.append(
            {
                "news_id": "yahoo_news_" + stable_hash("yahoo_finance_rss", ticker, title, published_at or link)[:20],
                "source_key": "yahoo_finance_rss",
                "source_name": "Yahoo Finance RSS",
                "title": title,
                "body": description,
                "url": link,
                "published_at": published_at,
                "tickers": [ticker],
                "market": infer_market([ticker]),
                "credibility": "medium",
                "metadata": {
                    "live": True,
                    "provider": "yahoo_finance",
                    "rss_symbol": symbol,
                    "source_url": url,
                },
            }
        )
    return items


def ingest_yahoo_finance_news(conn: sqlite3.Connection, tickers: list[str], limit: int = 20, timeout: int = 30) -> dict[str, Any]:
    inserted = 0
    deduped = 0
    errors: list[dict[str, str]] = []
    scanned = 0
    for ticker in tickers:
        try:
            items = fetch_yahoo_finance_news(ticker, limit=limit, timeout=timeout)
        except Exception as exc:
            errors.append({"ticker": ticker, "error": str(exc)})
            continue
        for item in items:
            scanned += 1
            result = upsert_news_item(conn, item)
            if result.get("deduped"):
                deduped += 1
            else:
                inserted += 1
    return {"inserted": inserted, "deduped": deduped, "scanned": scanned, "errors": errors, "source_key": "yahoo_finance_rss"}


def normalize_news_item(raw: dict[str, Any]) -> dict[str, Any]:
    title = normalize_text(raw.get("title") or raw.get("headline"), limit=500)
    if not title:
        raise ValueError("news title is required")
    body = normalize_text(raw.get("body") or raw.get("summary") or raw.get("description"), limit=12000)
    url = canonical_news_url(raw.get("url") or raw.get("source_url"))
    published_at = normalize_dt(raw.get("published_at") or raw.get("publish_time") or raw.get("date"))
    source_key = normalize_text(raw.get("source_key") or raw.get("source_kind") or "news_article", limit=120)
    source_name = normalize_text(raw.get("source_name") or raw.get("provider") or raw.get("media"), limit=240)
    tickers = raw.get("tickers") if isinstance(raw.get("tickers"), list) else infer_tickers(title, body, raw.get("entity_id"))
    themes = raw.get("themes") if isinstance(raw.get("themes"), list) else []
    entities = raw.get("entities") if isinstance(raw.get("entities"), list) else []
    market = infer_market(tickers, raw.get("market"))
    fingerprint = title_fingerprint(title)
    dedupe_hash = raw.get("dedupe_hash") or stable_hash(title, source_key, published_at or url or body[:240])
    news_id = raw.get("news_id") or f"news_{dedupe_hash[:20]}"
    return {
        "news_id": news_id,
        "source_key": source_key,
        "source_name": source_name,
        "title": title,
        "body": body,
        "url": url,
        "published_at": published_at,
        "ingested_at": normalize_dt(raw.get("ingested_at")) or now_ts(),
        "tickers": tickers,
        "themes": themes,
        "entities": entities,
        "language": raw.get("language") or ("zh" if re.search(r"[\u4e00-\u9fff]", title + body) else "en"),
        "market": market,
        "credibility": raw.get("credibility") or "medium",
        "dedupe_hash": dedupe_hash,
        "title_fingerprint": fingerprint,
        "source_list": raw.get("source_list") if isinstance(raw.get("source_list"), list) else [source_key],
        "metadata": raw.get("metadata") or {},
    }


def _merge_existing_news_item(
    conn: sqlite3.Connection,
    normalized: dict[str, Any],
    existing: sqlite3.Row | tuple[Any, ...],
) -> dict[str, Any]:
    source_list = loads_json(existing[1], [])
    for source_key in normalized["source_list"]:
        if source_key not in source_list:
            source_list.append(source_key)
    conn.execute(
        """
        UPDATE news_items
        SET source_list_json=?, ingested_at=?, metadata_json=?
        WHERE news_id=?
        """,
        (
            json.dumps(source_list, ensure_ascii=False),
            normalized["ingested_at"],
            json.dumps(normalized["metadata"], ensure_ascii=False, sort_keys=True),
            existing[0],
        ),
    )
    normalized["news_id"] = existing[0]
    normalized["deduped"] = True
    return normalized


def upsert_news_item(conn: sqlite3.Connection, item: dict[str, Any]) -> dict[str, Any]:
    ensure_news_tables(conn)
    normalized = normalize_news_item(item)
    publish_day = (normalized.get("published_at") or "")[:10]
    existing = conn.execute(
        """
        SELECT news_id, source_list_json
        FROM news_items
        WHERE dedupe_hash=?
           OR (url IS NOT NULL AND url != '' AND url=?)
           OR (title_fingerprint=? AND substr(COALESCE(published_at, ingested_at), 1, 10)=?)
        LIMIT 1
        """,
        (normalized["dedupe_hash"], normalized["url"], normalized["title_fingerprint"], publish_day),
    ).fetchone()
    if existing:
        return _merge_existing_news_item(conn, normalized, existing)

    try:
        conn.execute(
            """
            INSERT INTO news_items (
                news_id, source_key, source_name, title, body, url, published_at, ingested_at,
                tickers_json, themes_json, entities_json, language, market, credibility,
                dedupe_hash, title_fingerprint, source_list_json, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                normalized["news_id"],
                normalized["source_key"],
                normalized["source_name"],
                normalized["title"],
                normalized["body"],
                normalized["url"],
                normalized["published_at"],
                normalized["ingested_at"],
                json.dumps(normalized["tickers"], ensure_ascii=False),
                json.dumps(normalized["themes"], ensure_ascii=False),
                json.dumps(normalized["entities"], ensure_ascii=False),
                normalized["language"],
                normalized["market"],
                normalized["credibility"],
                normalized["dedupe_hash"],
                normalized["title_fingerprint"],
                json.dumps(normalized["source_list"], ensure_ascii=False),
                json.dumps(normalized["metadata"], ensure_ascii=False, sort_keys=True),
            ),
        )
        normalized["deduped"] = False
        return normalized
    except sqlite3.IntegrityError:
        existing = conn.execute(
            """
            SELECT news_id, source_list_json
            FROM news_items
            WHERE dedupe_hash=?
               OR (url IS NOT NULL AND url != '' AND url=?)
               OR (title_fingerprint=? AND substr(COALESCE(published_at, ingested_at), 1, 10)=?)
            LIMIT 1
            """,
            (normalized["dedupe_hash"], normalized["url"], normalized["title_fingerprint"], publish_day),
        ).fetchone()
        if not existing:
            raise
        return _merge_existing_news_item(conn, normalized, existing)


def count_live_news_for_ticker(conn: sqlite3.Connection, ticker: str, since_date: str | None = None) -> int:
    ensure_news_tables(conn)
    params: list[Any] = [f"%{ticker}%", f"%{ticker}%"]
    where = "(tickers_json LIKE ? OR metadata_json LIKE ?)"
    if since_date:
        where += " AND substr(COALESCE(published_at, ingested_at), 1, 10) >= ?"
        params.append(since_date)
    row = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM news_items
        WHERE {where}
          AND metadata_json LIKE '%"live"%'
        """,
        tuple(params),
    ).fetchone()
    return int(row[0] or 0)


def manifest_row_to_news(row: sqlite3.Row | tuple[Any, ...], columns: list[str]) -> dict[str, Any] | None:
    data = dict(row) if isinstance(row, sqlite3.Row) else {columns[index]: row[index] for index in range(len(row))}
    metadata = loads_json(data.get("metadata_json"), {})
    source_kind = metadata.get("source_kind") or data.get("source_type")
    if source_kind not in NEWS_SOURCE_KEYS and "news" not in str(source_kind):
        return None
    source_path = normalize_project_path(data.get("source_path")) if data.get("source_path") else None
    text = read_markdown(source_path) if source_path else ""
    return {
        "news_id": data.get("source_id"),
        "source_key": source_kind,
        "source_name": metadata.get("source_domain") or metadata.get("provider") or source_kind,
        "title": data.get("title"),
        "body": text,
        "url": metadata.get("source_url"),
        "published_at": metadata.get("published_at") or data.get("created_at") or data.get("updated_at"),
        "ingested_at": data.get("updated_at") or now_ts(),
        "tickers": [data.get("entity_id")] if data.get("entity_type") == "stock" else [],
        "market": metadata.get("market"),
        "metadata": {
            **metadata,
            "live": bool(metadata.get("live", True)),
            "source_id": data.get("source_id"),
            "source_rel_path": relative_to_project(source_path) if source_path else data.get("source_rel_path"),
        },
    }


def ingest_news_from_manifest(conn: sqlite3.Connection, limit: int | None = None) -> dict[str, Any]:
    ensure_news_tables(conn)
    if not relation_exists(conn, "source_manifest"):
        return {"inserted": 0, "deduped": 0, "skipped": 0, "scanned": 0, "reason": "source_manifest_missing"}
    wanted = [
        "source_id",
        "source_type",
        "entity_type",
        "entity_id",
        "title",
        "source_path",
        "source_rel_path",
        "status",
        "created_at",
        "updated_at",
        "metadata_json",
    ]
    available = table_columns(conn, "source_manifest")
    columns = [column for column in wanted if column in available]
    if "metadata_json" not in columns:
        return {"inserted": 0, "deduped": 0, "skipped": 0, "scanned": 0, "reason": "metadata_json_missing"}
    rows = conn.execute(
        f"""
        SELECT {', '.join(columns)}
        FROM source_manifest
        WHERE source_type='external_source_snapshot'
           OR metadata_json LIKE '%eastmoney_news%'
           OR metadata_json LIKE '%news_article%'
           OR metadata_json LIKE '%news_search%'
           OR metadata_json LIKE '%public_analyst_signal_marketscreener%'
           OR source_id LIKE '%eastmoney_news%'
           OR source_id LIKE '%news_article%'
           OR source_id LIKE '%news_search%'
        ORDER BY datetime(COALESCE(updated_at, created_at)) DESC, source_id DESC
        LIMIT ?
        """,
        (limit or 500,),
    ).fetchall()
    inserted = 0
    deduped = 0
    skipped = 0
    for row in rows:
        item = manifest_row_to_news(row, columns)
        if not item:
            skipped += 1
            continue
        try:
            result = upsert_news_item(conn, item)
        except ValueError:
            skipped += 1
            continue
        if result.get("deduped"):
            deduped += 1
        else:
            inserted += 1
    return {"inserted": inserted, "deduped": deduped, "skipped": skipped, "scanned": len(rows)}


def latest_news_by_source(conn: sqlite3.Connection, source_keys: set[str] | None = None) -> list[dict[str, Any]]:
    ensure_news_tables(conn)
    allowed_sources = source_keys or NEWS_SOURCE_KEYS
    placeholders = ",".join("?" for _ in allowed_sources)
    rows = conn.execute(
        f"""
        SELECT
            source_key,
            COALESCE(market, 'global') AS market,
            MAX(published_at) AS last_published_at,
            MAX(ingested_at) AS last_ingested_at,
            COUNT(*) AS item_count,
            COUNT(DISTINCT dedupe_hash) AS unique_count
        FROM news_items
        WHERE source_key IN ({placeholders})
        GROUP BY source_key, COALESCE(market, 'global')
        ORDER BY source_key, market
        """,
        tuple(sorted(allowed_sources)),
    ).fetchall()
    return [
        {
            "source_key": row[0],
            "market": row[1],
            "last_published_at": row[2],
            "last_ingested_at": row[3],
            "item_count": row[4],
            "unique_count": row[5],
        }
        for row in rows
    ]


def build_news_health_snapshot(
    conn: sqlite3.Connection,
    stale_after_minutes: int = 360,
    now: datetime | None = None,
    source_keys: set[str] | None = None,
) -> dict[str, Any]:
    now = now or datetime.now()
    rows = latest_news_by_source(conn, source_keys=source_keys)
    source_rows = []
    status_counts: dict[str, int] = {}
    for row in rows:
        anchor = parse_dt(row.get("last_published_at")) or parse_dt(row.get("last_ingested_at"))
        if not anchor:
            status = "missing"
            age_minutes = None
        else:
            age_minutes = max(0, int((now - anchor).total_seconds() / 60))
            status = "fresh" if age_minutes <= stale_after_minutes else "stale"
        status_counts[status] = status_counts.get(status, 0) + 1
        source_rows.append({**row, "freshness_status": status, "age_minutes": age_minutes})
    if not source_rows:
        overall = "missing"
    elif all(row["freshness_status"] == "fresh" for row in source_rows):
        overall = "fresh"
    elif any(row["freshness_status"] == "fresh" for row in source_rows):
        overall = "degraded"
    else:
        overall = "stale"
    return {
        "generated_at": now_ts(),
        "overall_status": overall,
        "stale_after_minutes": stale_after_minutes,
        "status_counts": status_counts,
        "source_rows": source_rows,
        "stale_sources": [row for row in source_rows if row["freshness_status"] != "fresh"],
    }


def update_news_health_rows(
    conn: sqlite3.Connection,
    stale_after_minutes: int = 360,
    affected_modules: list[str] | None = None,
    source_keys: set[str] | None = None,
) -> dict[str, Any]:
    from smr_data_health import ensure_data_health_tables, load_rules, rule_for

    ensure_news_tables(conn)
    ensure_data_health_tables(conn)
    affected_modules = affected_modules or ["deep_market_scan", "opportunity_radar", "report_generation"]
    # 读取 data_freshness_rules.json 中 news 的规则，取出 per-source 的 blocking_level 覆盖配置
    # 作用：让 manual_news 这类手动维护的源在过期时只 warn 而不 degrade，避免拖累整个机会雷达
    news_rule = rule_for("news", "global", load_rules())
    source_blocking_overrides = news_rule.get("source_blocking_overrides") or {}
    snapshot = build_news_health_snapshot(conn, stale_after_minutes=stale_after_minutes, source_keys=source_keys)
    rows = snapshot["source_rows"] or [
        {
            "source_key": "news",
            "market": "global",
            "last_published_at": None,
            "last_ingested_at": None,
            "freshness_status": "missing",
            "age_minutes": None,
            "item_count": 0,
            "unique_count": 0,
        }
    ]
    conn.execute("DELETE FROM data_source_health WHERE data_type='news'")
    timestamp = now_ts()
    for row in rows:
        status = row["freshness_status"]
        source_key = row.get("source_key") or "news"
        if status == "fresh":
            blocking = "none"
        else:
            # 过期时优先用 source_blocking_overrides 里配置的 blocking_level，没配置则默认 degrade
            blocking = source_blocking_overrides.get(source_key, "degrade")
        reason = ""
        if status != "fresh":
            reason = (
                f"news[{row.get('source_key')}/{row.get('market')}] stale or missing; "
                f"last_published_at={row.get('last_published_at') or '-'}, "
                f"last_ingested_at={row.get('last_ingested_at') or '-'}."
            )
        conn.execute(
            """
            INSERT INTO data_source_health (
                source_key, market, asset_type, data_type, last_success_at, last_data_timestamp,
                expected_update_frequency, freshness_status, stale_after_minutes, blocking_level,
                staleness_reason, affected_modules_json, metadata_json, created_at, updated_at
            )
            VALUES (?, ?, 'stock', 'news', ?, ?, 'intraday_batch', ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_key, market, asset_type, data_type) DO UPDATE SET
                last_success_at=excluded.last_success_at,
                last_data_timestamp=excluded.last_data_timestamp,
                freshness_status=excluded.freshness_status,
                stale_after_minutes=excluded.stale_after_minutes,
                blocking_level=excluded.blocking_level,
                staleness_reason=excluded.staleness_reason,
                affected_modules_json=excluded.affected_modules_json,
                metadata_json=excluded.metadata_json,
                updated_at=excluded.updated_at
            """,
            (
                row.get("source_key") or "news",
                row.get("market") or "global",
                row.get("last_ingested_at"),
                row.get("last_published_at") or row.get("last_ingested_at"),
                status,
                stale_after_minutes,
                blocking,
                reason,
                json.dumps(affected_modules, ensure_ascii=False),
                json.dumps(row, ensure_ascii=False, sort_keys=True),
                timestamp,
                timestamp,
            ),
        )
    return snapshot


def export_news_to_evidence(
    conn: sqlite3.Connection,
    limit: int = 50,
    min_credibility: set[str] | None = None,
    source_keys: set[str] | None = None,
) -> dict[str, Any]:
    ensure_news_tables(conn)
    ensure_claim_graph_tables(conn)
    min_credibility = min_credibility or {"medium", "high"}
    allowed_sources = source_keys or NEWS_SOURCE_KEYS
    placeholders = ",".join("?" for _ in min_credibility)
    source_placeholders = ",".join("?" for _ in allowed_sources)
    rows = conn.execute(
        f"""
        SELECT news_id, source_key, title, body, url, published_at, ingested_at,
               credibility, metadata_json, tickers_json, market
        FROM news_items
        WHERE credibility IN ({placeholders})
          AND source_key IN ({source_placeholders})
        ORDER BY datetime(COALESCE(published_at, ingested_at)) DESC, news_id DESC
        LIMIT ?
        """,
        (*sorted(min_credibility), *sorted(allowed_sources), limit),
    ).fetchall()
    exported = 0
    for row in rows:
        text = normalize_text(f"{row[2]}. {row[3] or ''}", limit=1200)
        if not text:
            continue
        source_key = row[1] or "news_article"
        evidence_id = "ev_" + stable_hash(source_key, row[0], text)[:16]
        tickers = loads_json(row[9], [])
        metadata = loads_json(row[8], {})
        if tickers and not metadata.get("ticker"):
            metadata["ticker"] = tickers[0]
        upsert_evidence(
            conn,
            {
                "evidence_id": evidence_id,
                "source_key": source_key,
                "source_type": "news",
                "source_quality": "secondary",
                "source_status": "active",
                "published_at": row[5],
                "ingested_at": row[6],
                "text_excerpt": text,
                "url_or_doc_id": row[4] or row[0],
                "metadata": {
                    **metadata,
                    "news_id": row[0],
                    "credibility": row[7],
                    "tickers": tickers,
                    "market": row[10],
                    "exporter": "smr_news_ingestion",
                },
            },
        )
        exported += 1
    return {"exported": exported, "scanned": len(rows)}


def seed_news_item(
    conn: sqlite3.Connection,
    title: str,
    body: str = "",
    source_key: str = "manual_news",
    published_at: str | None = None,
    ticker: str | None = None,
    market: str | None = None,
    credibility: str = "medium",
) -> dict[str, Any]:
    return upsert_news_item(
        conn,
        {
            "news_id": generate_execution_id("news_seed"),
            "source_key": source_key,
            "title": title,
            "body": body,
            "published_at": published_at or now_ts(),
            "tickers": [ticker] if ticker else [],
            "market": market,
            "credibility": credibility,
            "metadata": {"seeded": True},
        },
    )
