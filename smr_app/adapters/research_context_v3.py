from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


MAX_CHUNK_TEXT = 6_000
CHUNK_LIMIT = 36
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=?", (name,)
    ).fetchone() is not None


def _columns(conn: sqlite3.Connection, name: str) -> set[str]:
    if not _table_exists(conn, name):
        return set()
    return {str(row[1]) for row in conn.execute(f"PRAGMA table_info({name})")}


def _rows(conn: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    previous = conn.row_factory
    conn.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in conn.execute(sql, tuple(params)).fetchall()]
    finally:
        conn.row_factory = previous


def _json(value: Any, default: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if value in (None, ""):
        return default
    try:
        return json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def _stable_evidence_id(prefix: str, value: Any) -> str:
    token = re.sub(r"[^A-Za-z0-9_.:-]", "_", str(value or "unknown"))
    return f"{prefix}:{token}"[:128]


def provider_status(conn: sqlite3.Connection, control_conn: sqlite3.Connection) -> dict[str, Any]:
    capabilities = {
        "official_filings": ("filing_documents", "document_chunks"),
        "evidence": ("evidence_items",),
        "news": ("news_items",),
        "events": ("market_event",),
        "broker_research": ("source_manifest",),
        "sector_graph": ("stock_pool", "sector_config"),
        "instruments": ("daily_bar", "valuation_snapshot", "fundamentals_snapshot"),
        "memory": ("memory_items",),
    }
    result: dict[str, Any] = {}
    for capability, tables in capabilities.items():
        target = control_conn if capability == "memory" else conn
        available = [table for table in tables if _table_exists(target, table)]
        result[capability] = {
            "status": "available" if len(available) == len(tables) else "partial" if available else "unavailable",
            "available_tables": available,
            "missing_tables": [table for table in tables if table not in available],
        }
    return result


def _resolve_identity(conn: sqlite3.Connection, ticker: str, market: str) -> dict[str, Any]:
    identity = {"ticker": ticker, "market": market, "company_name": ticker, "sector_key": None, "sector_name": None}
    try:
        configured = json.loads(
            (PROJECT_ROOT / "config" / "cninfo_identities.json").read_text(encoding="utf-8")
        )
        configured_identity = (configured.get("identities") or {}).get(ticker) or {}
        if configured_identity.get("security_name"):
            identity["company_name"] = str(configured_identity["security_name"])
    except (OSError, json.JSONDecodeError):
        pass
    if _table_exists(conn, "filing_documents"):
        row = conn.execute(
            "SELECT company_name FROM filing_documents WHERE ticker=? AND company_name IS NOT NULL "
            "ORDER BY published_at DESC LIMIT 1", (ticker,)
        ).fetchone()
        if row and row[0]:
            identity["company_name"] = str(row[0])
    if _table_exists(conn, "stock_pool"):
        row = conn.execute(
            "SELECT sector FROM stock_pool WHERE ts_code=? AND sector IS NOT NULL "
            "ORDER BY added_date DESC LIMIT 1", (ticker,)
        ).fetchone()
        if row:
            identity["sector_key"] = row[0]
    if identity["sector_key"] and _table_exists(conn, "sector_config"):
        row = conn.execute(
            "SELECT sector_name FROM sector_config WHERE sector_key=? LIMIT 1", (identity["sector_key"],)
        ).fetchone()
        if row:
            identity["sector_name"] = row[0]
    return identity


def _filings(conn: sqlite3.Connection, ticker: str) -> list[dict[str, Any]]:
    if not _table_exists(conn, "filing_documents"):
        return []
    return _rows(
        conn,
        "SELECT filing_id,ticker,market,company_name,filing_type,title,published_at,source_key,source_url,parse_status "
        "FROM filing_documents WHERE ticker=? ORDER BY published_at DESC LIMIT 16",
        (ticker,),
    )


KEYWORD_GROUPS = {
    "business": ("主要业务", "主营业务", "经营模式", "销售模式", "生产模式"),
    "products": ("主要产品", "800G", "1.6T", "硅光", "产品系列"),
    "operations": ("产能", "产量", "销量", "毛利率", "客户认证", "供应商"),
    "financials": ("主要会计数据", "营业收入", "净利润", "现金流量", "资产负债表", "利润表"),
    "industry": ("行业", "市场份额", "数据中心", "云计算", "竞争格局"),
    "risks": ("风险", "不利", "依赖", "波动", "减值"),
    "growth": ("未来", "研发", "募投", "扩产", "需求", "增长"),
}


def _chunk_score(row: dict[str, Any]) -> tuple[float, set[str]]:
    text = f"{row.get('section_name') or ''}\n{row.get('text') or ''}"
    matched = {group for group, terms in KEYWORD_GROUPS.items() if any(term in text for term in terms)}
    numeric = max(float(row.get(name) or 0.0) for name in (
        "investment_relevance_score", "financial_table_score", "guidance_relevance_score",
        "risk_relevance_score", "business_update_score",
    ))
    return numeric + min(len(matched), 4) * 0.2, matched


def _chunks(conn: sqlite3.Connection, ticker: str) -> list[dict[str, Any]]:
    if not _table_exists(conn, "document_chunks"):
        return []
    available = _columns(conn, "document_chunks")
    required = {"chunk_id", "document_id", "document_type", "source_key", "ticker", "market", "section_name", "chunk_index", "text", "evidence_id"}
    if not required.issubset(available):
        return []
    optional_defaults = {
        "chunk_section_type": "NULL",
        "investment_relevance_score": "0.0",
        "financial_table_score": "0.0",
        "guidance_relevance_score": "0.0",
        "risk_relevance_score": "0.0",
        "business_update_score": "0.0",
        "exclude_reason": "NULL",
        "usable_for_core_claim": "0",
    }
    select_columns = [
        "chunk_id", "document_id", "document_type", "source_key", "ticker", "market",
        "section_name", "chunk_index", "text", "evidence_id",
        *[
            name if name in available else f"{default} AS {name}"
            for name, default in optional_defaults.items()
        ],
    ]
    exclusion_filter = " AND COALESCE(exclude_reason,'')=''" if "exclude_reason" in available else ""
    rows = _rows(
        conn,
        f"SELECT {','.join(select_columns)} FROM document_chunks WHERE ticker=?{exclusion_filter}",
        (ticker,),
    )
    ranked = []
    for row in rows:
        preview = str(row.get("text") or "")[:1_000]
        section_name = str(row.get("section_name") or "")
        noisy_financial_section = any(token in section_name for token in (
            "资产负债表", "利润表", "现金流量表", "所有者权益变动表", "财务报表附注", "内部控制",
        ))
        if "内部控制" in preview and not any(term in preview for term in ("主营业务", "主要产品", "营业收入")):
            continue
        score, groups = _chunk_score(row)
        if noisy_financial_section:
            groups.intersection_update({"financials", "risks"})
            if not groups:
                continue
        if score <= 0 and not groups:
            continue
        row["research_topics"] = sorted(groups)
        row["retrieval_score"] = round(score, 4)
        row["text"] = str(row.get("text") or "")[:MAX_CHUNK_TEXT]
        ranked.append(row)
    ranked.sort(key=lambda item: (item["retrieval_score"], len(item["text"])), reverse=True)

    selected: list[dict[str, Any]] = []
    seen = set()
    by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in ranked:
        for topic in row["research_topics"]:
            by_topic[topic].append(row)
    for topic in KEYWORD_GROUPS:
        for row in by_topic.get(topic, [])[:3]:
            if row["chunk_id"] not in seen:
                selected.append(row)
                seen.add(row["chunk_id"])
    for row in ranked:
        if len(selected) >= CHUNK_LIMIT:
            break
        if row["chunk_id"] not in seen:
            selected.append(row)
            seen.add(row["chunk_id"])
    return selected[:CHUNK_LIMIT]


def _news(conn: sqlite3.Connection, ticker: str) -> list[dict[str, Any]]:
    if not _table_exists(conn, "news_items"):
        return []
    rows = _rows(
        conn,
        "SELECT news_id,source_key,source_name,title,body,url,published_at,credibility,tickers_json,themes_json "
        "FROM news_items WHERE tickers_json LIKE ? ORDER BY published_at DESC LIMIT 20",
        (f"%{ticker}%",),
    )
    for row in rows:
        row["body"] = str(row.get("body") or "")[:1_200]
        row["evidence_id"] = _stable_evidence_id("news", row.get("news_id"))
        row["allowed_usage"] = "context_only"
    return rows


def _events(conn: sqlite3.Connection, ticker: str) -> list[dict[str, Any]]:
    if not _table_exists(conn, "market_event"):
        return []
    rows = _rows(
        conn,
        "SELECT event_id,source_key,event_family,event_type,title,event_date,publish_time,importance,status,source_path "
        "FROM market_event WHERE entity_id=? ORDER BY event_date DESC LIMIT 20",
        (ticker,),
    )
    for row in rows:
        row["evidence_id"] = _stable_evidence_id("event", row.get("event_id"))
        row["allowed_usage"] = "event_context"
    return rows


def _database_project_root(conn: sqlite3.Connection) -> Path | None:
    try:
        rows = conn.execute("PRAGMA database_list").fetchall()
    except sqlite3.Error:
        return None
    for row in rows:
        path = Path(str(row[2] or ""))
        if not path.is_absolute() or not path.exists():
            continue
        for parent in path.parents:
            if (parent / "11_smr_wiki").is_dir():
                return parent
    return None


def _frontmatter_value(text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", text)
    return match.group(1).strip() if match else None


def _broker_reports(conn: sqlite3.Connection, ticker: str) -> list[dict[str, Any]]:
    if not _table_exists(conn, "source_manifest"):
        return []
    root = _database_project_root(conn)
    if root is None:
        return []
    rows = _rows(
        conn,
        "SELECT source_id,source_type,entity_id,title,source_path,source_rel_path,status,tags,metadata_json "
        "FROM source_manifest WHERE entity_id=? AND status='active' "
        "AND (tags LIKE '%research_article%' OR metadata_json LIKE '%research_article%') "
        "ORDER BY created_at DESC LIMIT 8",
        (ticker,),
    )
    output = []
    seen = set()
    for row in rows:
        relative = str(row.get("source_rel_path") or "").replace("\\", "/")
        path = root / relative if relative else Path(str(row.get("source_path") or ""))
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        info_code = _frontmatter_value(raw, "info_code") or str(row.get("source_id") or "")
        if info_code in seen:
            continue
        seen.add(info_code)
        extracted = raw.split("## Extracted Text", 1)[-1].strip()
        title_match = re.search(r"(?m)^#\s+(.+)$", raw)
        short_name = None
        name_match = re.search(r"(?m)^证券简称：\s*([^\s]+)", extracted)
        if name_match:
            short_name = name_match.group(1).strip()
        topics = {
            group for group, terms in KEYWORD_GROUPS.items()
            if any(term in extracted for term in terms)
        }
        output.append({
            "report_id": info_code,
            "source_id": row.get("source_id"),
            "title": title_match.group(1).strip() if title_match else str(row.get("title") or ticker),
            "company_name": short_name,
            "published_at": _frontmatter_value(raw, "published_at"),
            "source_name": _frontmatter_value(raw, "org_name") or "券商公开研报",
            "researcher": _frontmatter_value(raw, "researcher"),
            "rating": _frontmatter_value(raw, "rating_name"),
            "url": _frontmatter_value(raw, "source_url"),
            "pdf_url": _frontmatter_value(raw, "pdf_url"),
            "text": extracted[:16_000],
            "research_topics": sorted(topics),
            "evidence_id": _stable_evidence_id("broker", info_code),
            "allowed_usage": "secondary_context_only",
            "source_tier": "secondary_research",
        })
    return output


def _memories(conn: sqlite3.Connection, ticker: str) -> list[dict[str, Any]]:
    cols = _columns(conn, "memory_items")
    if not cols:
        return []
    entity_col = "entity_id" if "entity_id" in cols else "ticker" if "ticker" in cols else None
    if not entity_col:
        return []
    wanted = [name for name in (
        "memory_id", "entity_type", entity_col, "memory_type", "content_json", "content",
        "status", "confidence", "created_at", "updated_at",
    ) if name in cols]
    status_filter = " AND status IN ('approved','candidate')" if "status" in cols else ""
    order = "updated_at" if "updated_at" in cols else "created_at" if "created_at" in cols else wanted[0]
    rows = _rows(
        conn,
        f"SELECT {','.join(wanted)} FROM memory_items WHERE {entity_col}=?{status_filter} ORDER BY {order} DESC LIMIT 12",
        (ticker,),
    )
    for row in rows:
        if "content_json" in row:
            row["content"] = _json(row.pop("content_json"), row.get("content_json"))
        row["allowed_usage"] = "research_context"
    return rows


def _normalize_peer(code: str) -> str:
    value = code.strip().upper()
    if not value or "." in value or re.fullmatch(r"[A-Z][A-Z0-9.-]{0,9}", value):
        return value
    if re.fullmatch(r"\d{5}", value):
        return value + ".HK"
    if re.fullmatch(r"\d{6}", value):
        if value.startswith(("4", "8")):
            return value + ".BJ"
        return value + (".SH" if value.startswith(("5", "6", "9")) else ".SZ")
    return value


def _graph(conn: sqlite3.Connection, identity: dict[str, Any]) -> dict[str, Any]:
    sector = {}
    peers: list[str] = []
    benchmarks: list[str] = []
    key = identity.get("sector_key")
    if key and _table_exists(conn, "sector_config"):
        rows = _rows(conn, "SELECT * FROM sector_config WHERE sector_key=? LIMIT 1", (key,))
        if rows:
            sector = rows[0]
            peers = [_normalize_peer(item) for item in str(sector.get("ah_universe") or "").split(",")]
            benchmarks = [_normalize_peer(item) for item in str(sector.get("us_benchmarks") or "").split(",")]
    ticker = identity["ticker"]
    peers = [item for item in peers if item and item != ticker]
    return {"sector": sector, "peers": peers[:8], "us_benchmarks": benchmarks[:6]}


def _instrument(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    result: dict[str, Any] = {"ticker": ticker, "daily_bars": [], "valuation": None, "fundamentals": None}
    if _table_exists(conn, "daily_bar"):
        result["daily_bars"] = _rows(
            conn,
            "SELECT trade_date,open,close,high,low,vol,amount,pct_chg,turnover,market "
            "FROM daily_bar WHERE ts_code=? ORDER BY trade_date DESC LIMIT 20", (ticker,),
        )
    if _table_exists(conn, "valuation_snapshot"):
        rows = _rows(conn, "SELECT * FROM valuation_snapshot WHERE ticker=? ORDER BY generated_at DESC LIMIT 1", (ticker,))
        result["valuation"] = rows[0] if rows else None
    if _table_exists(conn, "fundamentals_snapshot"):
        rows = _rows(conn, "SELECT * FROM fundamentals_snapshot WHERE ticker=? ORDER BY created_at DESC LIMIT 1", (ticker,))
        result["fundamentals"] = rows[0] if rows else None
    if _table_exists(conn, "filing_documents"):
        row = conn.execute(
            "SELECT company_name FROM filing_documents WHERE ticker=? AND company_name IS NOT NULL ORDER BY published_at DESC LIMIT 1",
            (ticker,),
        ).fetchone()
        if row:
            result["company_name"] = row[0]
    return result


def resolve_stock_research_identity(
    source_conn: sqlite3.Connection, *, ticker: str, market: str
) -> dict[str, Any]:
    return _resolve_identity(source_conn, ticker, market)


def collect_stock_official_corpus(source_conn: sqlite3.Connection, *, ticker: str) -> dict[str, Any]:
    return {
        "filings": _filings(source_conn, ticker),
        "chunks": _chunks(source_conn, ticker),
        "broker_reports": _broker_reports(source_conn, ticker),
    }


def collect_stock_memory(control_conn: sqlite3.Connection, *, ticker: str) -> list[dict[str, Any]]:
    return _memories(control_conn, ticker)


def collect_stock_news_events(source_conn: sqlite3.Connection, *, ticker: str) -> dict[str, Any]:
    return {"news": _news(source_conn, ticker), "events": _events(source_conn, ticker)}


def collect_stock_industry_graph(
    source_conn: sqlite3.Connection, *, identity: dict[str, Any]
) -> dict[str, Any]:
    return _graph(source_conn, identity)


def collect_stock_instruments(
    source_conn: sqlite3.Connection,
    *,
    ticker: str,
    graph: dict[str, Any],
) -> dict[str, Any]:
    peer_codes = [*graph.get("peers", [])[:5], *graph.get("us_benchmarks", [])[:3]]
    return {
        "target": _instrument(source_conn, ticker),
        "peers": [_instrument(source_conn, code) for code in peer_codes if code],
    }


def assemble_stock_research_context(
    *,
    provider_health: dict[str, Any],
    identity: dict[str, Any],
    official_corpus: dict[str, Any],
    memories: list[dict[str, Any]],
    news_events: dict[str, Any],
    graph: dict[str, Any],
    instruments: dict[str, Any],
) -> dict[str, Any]:
    identity = dict(identity)
    ticker = str(identity["ticker"])
    filings = official_corpus.get("filings") or []
    chunks = official_corpus.get("chunks") or []
    broker_reports = official_corpus.get("broker_reports") or []
    if identity["company_name"] == ticker:
        for filing in filings:
            title = str(filing.get("title") or "")
            match = re.search(r"\d{4}-\d{2}-\d{2}\s+([^：:]{2,24})[：:]", title)
            if not match:
                match = re.search(r"([\u4e00-\u9fff]{2,24}(?:股份)?有限公司)", title)
            if match:
                identity["company_name"] = match.group(1).strip()
                break
    if identity["company_name"] == ticker:
        for report in broker_reports:
            if report.get("company_name"):
                identity["company_name"] = str(report["company_name"])
                break
    if identity["company_name"] == ticker:
        for chunk in chunks:
            match = re.search(r"([\u4e00-\u9fff]{2,24}(?:股份)?有限公司)", str(chunk.get("text") or ""))
            if match:
                identity["company_name"] = match.group(1)
                break
    return {
        "provider_status": provider_health,
        "identity": identity,
        "corpus": {
            **official_corpus,
            **news_events,
            "memories": memories,
        },
        "graph": graph,
        "instruments": instruments,
    }


def collect_stock_research_context(
    source_conn: sqlite3.Connection,
    control_conn: sqlite3.Connection,
    *,
    ticker: str,
    market: str,
) -> dict[str, Any]:
    identity = resolve_stock_research_identity(source_conn, ticker=ticker, market=market)
    official = collect_stock_official_corpus(source_conn, ticker=ticker)
    graph = collect_stock_industry_graph(source_conn, identity=identity)
    return assemble_stock_research_context(
        provider_health=provider_status(source_conn, control_conn),
        identity=identity,
        official_corpus=official,
        memories=collect_stock_memory(control_conn, ticker=ticker),
        news_events=collect_stock_news_events(source_conn, ticker=ticker),
        graph=graph,
        instruments=collect_stock_instruments(source_conn, ticker=ticker, graph=graph),
    )
