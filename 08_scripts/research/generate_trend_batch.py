#!/usr/bin/env python3
"""Generate dynamic SMR trend research artifacts from latest local snapshots."""

import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import ensure_auto_handoff
from smr_paths import project_path, relative_to_project
from smr_registry import register_snapshot
from smr_universe import load_active_equity_universe
from smr_runlog import log_run
from smr_wiki import ensure_source_manifest_table

ROOT = project_path()
DB_PATH = project_path("01_data", "db", "smr.db")
FACTOR_DIR = project_path("01_data", "factor")
INDUSTRY_ROOT = project_path("02_research", "industry")
STOCK_DIR = project_path("02_research", "stock")
DRAFT_ROOT = project_path("02_research", "drafts")

INDUSTRY_DIR_MAP = {
    "semiconductor_photonics": "semiconductor",
    "semiconductor_compute": "semiconductor",
}

SECTOR_REPORT_TITLES = {
    "semiconductor_photonics": "光模块/CPO",
    "semiconductor_compute": "半导体/算力",
    "embodied_ai": "具身智能/机器人",
    "ai_agent": "AI应用",
    "quantum": "量子",
}

SECTOR_LINKAGE_TEXT = {
    "semiconductor_photonics": "光通信与 AI 互联景气映射",
    "semiconductor_compute": "算力资本开支映射",
    "embodied_ai": "机器人产业链景气映射",
    "ai_agent": "AI 应用景气映射",
    "quantum": "量子主题映射",
}

SOURCE_TYPE_PRIORITY = {
    "external_source_snapshot": 0,
    "recommendation_card": 1,
    "stock_research": 2,
    "industry_research": 3,
    "industry_research_current_batch": 4,
}
EXTERNAL_SOURCE_KIND_PRIORITY = {
    "research_table_structured": 0,
    "research_structured": 1,
    "research_pdf_text": 2,
    "research_article": 3,
    "research_search": 4,
    "announcement": 5,
    "news_article": 6,
    "news_search": 7,
}


def local_bundle_source(label, detail, rel_path=None, source_type="local_truth"):
    return {
        "source_type": source_type,
        "title": label,
        "detail": detail,
        "source_rel_path": rel_path,
        "source_path": str(project_path(rel_path)) if rel_path and not rel_path.startswith("/") else rel_path,
        "updated_at": None,
        "entity_id": None,
    }


def supporting_bundle_source(source_type, title, rel_path=None, source_path=None, updated_at=None, entity_id=None, detail=None):
    return {
        "source_type": source_type,
        "title": title,
        "detail": detail,
        "source_rel_path": rel_path,
        "source_path": source_path,
        "updated_at": updated_at,
        "entity_id": entity_id,
        "source_kind": None,
    }


def build_base_local_sources(latest_ah, latest_us, latest_factor, summary_path):
    return [
        local_bundle_source("本机 A/H 行情真相层", f"`daily_bar` @ {latest_ah}", rel_path="01_data/db/smr.db"),
        local_bundle_source("本机因子真相层", f"`factor_daily` @ {latest_factor}", rel_path="01_data/db/smr.db"),
        local_bundle_source("本机美股联动真相层", f"`us_daily_bar` @ {latest_us}", rel_path="01_data/db/smr.db"),
        local_bundle_source(
            "本机趋势汇总快照",
            f"最新趋势批量汇总 `trend_analysis_{latest_ah}.md`",
            rel_path=relative_to_project(summary_path),
            source_type="local_snapshot",
        ),
    ]


def parse_metadata_json(text):
    try:
        return json.loads(text or "{}")
    except json.JSONDecodeError:
        return {}


def collect_supporting_sources(conn, entity_ids, allowed_types, limit=8, exclude_rel_paths=None):
    ensure_source_manifest_table(conn)
    entity_ids = [value for value in entity_ids if value]
    allowed_types = [value for value in allowed_types if value]
    if not entity_ids or not allowed_types:
        return []

    exclude_rel_paths = set(exclude_rel_paths or [])
    entity_placeholders = ",".join("?" for _ in entity_ids)
    type_placeholders = ",".join("?" for _ in allowed_types)
    rows = conn.execute(
        f"""
        SELECT source_type, entity_id, title, source_path, source_rel_path, updated_at, metadata_json
        FROM source_manifest
        WHERE status='active'
          AND entity_id IN ({entity_placeholders})
          AND source_type IN ({type_placeholders})
        ORDER BY datetime(updated_at) DESC, datetime(created_at) DESC, source_id DESC
        """,
        [*entity_ids, *allowed_types],
    ).fetchall()

    collected = []
    seen = set()
    for source_type, entity_id, title, source_path, source_rel_path, updated_at, metadata_json in rows:
        if source_rel_path in exclude_rel_paths:
            continue
        path_obj = Path(source_path)
        if not path_obj.exists():
            continue
        dedupe_key = (source_type, source_rel_path)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        metadata = parse_metadata_json(metadata_json)
        source_kind = metadata.get("source_kind")
        detail = None
        if source_type == "external_source_snapshot" and source_kind:
            detail = source_kind
        collected.append(
            {
                "source_type": source_type,
                "title": title,
                "detail": detail,
                "source_rel_path": source_rel_path,
                "source_path": source_path,
                "updated_at": updated_at,
                "entity_id": entity_id,
                "source_kind": source_kind,
            }
        )

    collected.sort(key=lambda item: item.get("updated_at") or "", reverse=True)
    collected.sort(
        key=lambda item: (
            SOURCE_TYPE_PRIORITY.get(item["source_type"], 99),
            EXTERNAL_SOURCE_KIND_PRIORITY.get(item.get("source_kind"), 99),
        )
    )
    return collected[:limit]


def build_source_bundle(base_sources, supporting_sources):
    return {
        "base_sources": base_sources,
        "supporting_sources": supporting_sources,
        "gate_passed": bool(supporting_sources),
    }


def render_source_section(source_bundle):
    lines = ["## Data Sources", "", "### Base Local Sources"]
    for item in source_bundle["base_sources"]:
        detail = item["detail"]
        if item.get("source_rel_path"):
            detail += f" | {item['source_rel_path']}"
        lines.append(f"- {item['title']}：{detail}")

    lines.extend(["", "### Supporting Local Sources"])
    if not source_bundle["supporting_sources"]:
        lines.append("- 无。当前批次没有找到可直接复核的本机支持来源，因此只允许输出草稿。")
    else:
        for item in source_bundle["supporting_sources"]:
            detail = item.get("detail") or item["title"]
            if item.get("source_rel_path"):
                detail += f" | {item['source_rel_path']}"
            lines.append(f"- {item['source_type']}：{detail}")
    lines.append("")
    return "\n".join(lines)


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


def latest_external_research_snapshot(conn, ts_code):
    rows = conn.execute(
        """
        SELECT title, source_rel_path, metadata_json, updated_at
        FROM source_manifest
        WHERE status='active'
          AND source_type='external_source_snapshot'
          AND entity_id=?
          AND json_extract(metadata_json, '$.source_kind') IN ('research_table_structured', 'research_structured')
        ORDER BY
            CASE json_extract(metadata_json, '$.source_kind')
                WHEN 'research_table_structured' THEN 0
                WHEN 'research_structured' THEN 1
                ELSE 9
            END ASC,
            datetime(updated_at) DESC,
            source_id DESC
        LIMIT 4
        """,
        (ts_code,),
    ).fetchall()

    for title, source_rel_path, metadata_json, updated_at in rows:
        metadata = parse_metadata_json(metadata_json)
        raw_payload = load_json_rel_path(metadata.get("raw_rel_path"))
        if not raw_payload:
            continue

        source_kind = metadata.get("source_kind")
        if source_kind == "research_table_structured":
            normalized = raw_payload.get("forecast_table", {}).get("normalized_metrics", {})
            rating = raw_payload.get("rating", {})
            document = raw_payload.get("document", {})
            return {
                "source_kind": source_kind,
                "title": title,
                "source_rel_path": source_rel_path,
                "updated_at": updated_at,
                "published_at": document.get("published_at"),
                "org_name": document.get("org_name"),
                "rating_name": document.get("rating_name"),
                "target_price_yuan": rating.get("target_price_yuan"),
                "eps_yuan": normalized.get("eps_yuan", {}),
                "pe_multiple": normalized.get("pe_multiple", {}),
                "net_profit_billion": normalized.get("net_profit_billion", {}),
                "revenue_billion": normalized.get("revenue_billion", {}),
                "roe_percent": normalized.get("roe_percent", {}),
            }

        if source_kind == "research_structured":
            metrics = raw_payload.get("forecast_metrics", {})
            document = raw_payload.get("document", {})
            return {
                "source_kind": source_kind,
                "title": title,
                "source_rel_path": source_rel_path,
                "updated_at": updated_at,
                "published_at": document.get("published_at"),
                "org_name": document.get("org_name"),
                "rating_name": document.get("rating_name"),
                "target_price_yuan": metrics.get("target_price_yuan"),
                "eps_yuan": metrics.get("eps_yuan", {}),
                "pe_multiple": metrics.get("pe_multiple", {}),
                "net_profit_billion": metrics.get("net_profit_billion", {}),
                "revenue_billion": metrics.get("revenue_billion", {}),
                "roe_percent": {},
            }
    return None


def render_external_research_section(research_snapshot):
    if not research_snapshot:
        return "\n".join(
            [
                "## Latest External Research Snapshot",
                "",
                "- 当前没有可直接引用的 `research_table_structured / research_structured` 快照。",
                "",
            ]
        )

    lines = [
        "## Latest External Research Snapshot",
        "",
        f"- source_kind: {research_snapshot['source_kind']}",
        f"- title: {research_snapshot['title']}",
        f"- org_name: {research_snapshot.get('org_name') or '-'}",
        f"- published_at: {research_snapshot.get('published_at') or '-'}",
        f"- rating_name: {research_snapshot.get('rating_name') or '-'}",
        f"- target_price_yuan: {research_snapshot.get('target_price_yuan') if research_snapshot.get('target_price_yuan') is not None else '-'}",
    ]
    for label, key in (
        ("revenue_billion", "revenue_billion"),
        ("net_profit_billion", "net_profit_billion"),
        ("eps_yuan", "eps_yuan"),
        ("pe_multiple", "pe_multiple"),
        ("roe_percent", "roe_percent"),
    ):
        values = research_snapshot.get(key) or {}
        if values:
            lines.append(f"- {label}: {json.dumps(values, ensure_ascii=False)}")
    if research_snapshot.get("source_rel_path"):
        lines.append(f"- source_rel_path: {research_snapshot['source_rel_path']}")
    lines.append("")
    return "\n".join(lines)


def write_source_bundle_file(report_dir, source_bundle):
    source_path = report_dir / "90_sources.md"
    write_text(source_path, "\n".join(["# Source Bundle", "", render_source_section(source_bundle)]))
    return source_path


def write_source_gate_draft(report_id, title, created_at, reason, context_lines, source_bundle):
    draft_dir = DRAFT_ROOT / report_id
    draft_path = draft_dir / "00_research-draft.md"
    lines = [
        "---",
        f"report_id: {report_id}",
        "draft_type: research_source_gate",
        f"title: {title}",
        f"created_at: {created_at}",
        "status: draft_missing_local_source",
        "---",
        "",
        f"# {title}（草稿）",
        "",
        "## 阻断原因",
        "",
        f"- {reason}",
        "",
        "## 当前上下文",
        "",
    ]
    lines.extend(f"- {line}" for line in context_lines)
    lines.extend(["", render_source_section(source_bundle)])
    write_text(draft_path, "\n".join(lines))
    return draft_path

def sector_config(conn):
    rows = conn.execute(
        """
        SELECT sector_key, sector_name, us_benchmarks
        FROM sector_config
        """
    ).fetchall()
    return {
        sector_key: {"sector_name": sector_name, "us_benchmarks": (us_benchmarks or "").split(",")}
        for sector_key, sector_name, us_benchmarks in rows
    }


def latest_dates(conn):
    latest_ah = conn.execute("SELECT max(trade_date) FROM daily_bar").fetchone()[0]
    latest_us = conn.execute("SELECT max(trade_date) FROM us_daily_bar").fetchone()[0]
    latest_factor = conn.execute("SELECT max(trade_date) FROM factor_daily").fetchone()[0]
    return latest_ah, latest_us, latest_factor


def load_snapshots(conn, registry_meta, latest_ah, latest_factor):
    daily_rows = conn.execute(
        """
        SELECT ts_code, close, pct_chg
        FROM daily_bar
        WHERE trade_date = ?
        """,
        (latest_ah,),
    ).fetchall()
    factor_rows = conn.execute(
        """
        SELECT ts_code, factor_name, factor_value
        FROM factor_daily
        WHERE trade_date = ?
        """,
        (latest_factor,),
    ).fetchall()

    snapshots = {}
    for ts_code, meta in registry_meta.items():
        snapshots[ts_code] = {
            "ts_code": ts_code,
            "name": meta["name"],
            "sector": meta["sector"],
            "market": meta["market"],
            "trade_date": latest_ah,
            "us_links": {},
        }

    for ts_code, close, pct_chg in daily_rows:
        if ts_code in snapshots:
            snapshots[ts_code]["close"] = close
            snapshots[ts_code]["pct_chg"] = pct_chg

    for ts_code, factor_name, factor_value in factor_rows:
        if ts_code not in snapshots:
            continue
        if factor_name.startswith("us_linkage_"):
            snapshots[ts_code]["us_links"][factor_name.replace("us_linkage_", "").upper()] = factor_value
        else:
            snapshots[ts_code][factor_name] = factor_value

    return snapshots


def select_targets(snapshots, min_trend_strength=2.0, limit=5):
    ranked = []
    for snapshot in snapshots.values():
        trend_strength = snapshot.get("trend_strength")
        if trend_strength is None or trend_strength < min_trend_strength:
            continue
        if snapshot.get("close") is None:
            continue
        us_link_total = sum(snapshot.get("us_links", {}).values())
        ranked.append(
            (
                trend_strength,
                us_link_total,
                snapshot.get("pct_chg") or 0.0,
                snapshot,
            )
        )

    ranked.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    return [item[3] for item in ranked[:limit]]


def latest_us_moves(conn):
    rows = conn.execute(
        """
        WITH latest AS (SELECT max(trade_date) AS d FROM us_daily_bar)
        SELECT symbol, pct_chg, close
        FROM us_daily_bar
        WHERE trade_date = (SELECT d FROM latest)
          AND symbol IN ('NVDA', 'LITE', 'COHR', 'MRVL', 'AMD', 'TSLA', 'IONQ')
        ORDER BY abs(pct_chg) DESC
        """
    ).fetchall()
    return rows


def trend_direction(snapshot):
    trend_strength = snapshot.get("trend_strength") or 0.0
    if trend_strength >= 3:
        return "uptrend"
    if trend_strength >= 2:
        return "moderate_uptrend"
    return "sideways"


def valuation_assessment(snapshot):
    pe = snapshot.get("pe_ttm") or 0.0
    pb = snapshot.get("pb") or 0.0
    if pe >= 120 or pb >= 35:
        return "speculative"
    if pe >= 80 or pb >= 20:
        return "overvalued"
    if pe >= 40 or pb >= 8:
        return "fair_to_full"
    return "fair"


def suggested_pool(snapshot):
    if (snapshot.get("trend_strength") or 0.0) >= 3:
        return "candidate"
    return "watchlist"


def us_ref_list(snapshot, sector_meta):
    refs = sorted(snapshot.get("us_links", {}).items(), key=lambda item: item[1], reverse=True)
    if refs:
        return [symbol for symbol, _value in refs]
    return [symbol for symbol in sector_meta.get("us_benchmarks", []) if symbol][:2]


def write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def write_factor_summary(created_at, latest_ah, latest_us, targets, us_moves):
    FACTOR_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = FACTOR_DIR / f"trend_analysis_{latest_ah}.md"
    lines = [
        f"# SMR 趋势快照 - {latest_ah}",
        "",
        f"- generated_at: {created_at}",
        f"- latest_ah_date: {latest_ah}",
        f"- latest_us_date: {latest_us}",
        "- method: dynamic ranking by trend_strength + US linkage + pct_chg",
        "",
        "## 动态入选标的",
        "",
        "| ts_code | name | sector | direction | trend_strength | pct_chg | US linkage | suggested_pool |",
        "|---------|------|--------|-----------|----------------|--------:|------------|----------------|",
    ]
    for snapshot in targets:
        us_linkage = ", ".join(f"{symbol} {value:.2f}" for symbol, value in snapshot.get("us_links", {}).items())
        lines.append(
            f"| {snapshot['ts_code']} | {snapshot['name']} | {snapshot['sector']} | {trend_direction(snapshot)} | "
            f"{snapshot['trend_strength']:.0f} | {(snapshot.get('pct_chg') or 0.0):.2f}% | {us_linkage or '-'} | {suggested_pool(snapshot)} |"
        )

    lines.extend(
        [
            "",
            "## 美股联动背景",
            "",
            "| symbol | pct_chg | close |",
            "|--------|--------:|------:|",
        ]
    )
    for symbol, pct_chg, close in us_moves:
        lines.append(f"| {symbol} | {pct_chg:.2f}% | {close:.2f} |")

    lines.extend(
        [
            "",
            "## 结论",
            "",
            "- 当前批量研究对象不再写死，而是由最新趋势和联动因子自动选择。",
            "- 后续股票池应优先使用研究卡中的 `Suggested Pool` 和动态池重建脚本同步，而不是把注册表当成固定关注名单。",
        ]
    )
    write_text(summary_path, "\n".join(lines))
    return summary_path


def dominant_sector(targets):
    counter = Counter(snapshot["sector"] for snapshot in targets)
    return counter.most_common(1)[0][0]


def industry_report_dir(sector_key):
    return INDUSTRY_ROOT / INDUSTRY_DIR_MAP.get(sector_key, sector_key)


def write_industry_pack(conn, created_at, latest_ah, latest_us, latest_factor, summary_path, targets, us_moves, sector_key, sector_meta):
    report_id = f"{latest_ah}_{sector_key}_trend_snapshot"
    report_dir = industry_report_dir(sector_key) / report_id
    card_path = report_dir / "00_research-card.md"

    sector_targets = [snapshot for snapshot in targets if snapshot["sector"] == sector_key]
    sector_title = SECTOR_REPORT_TITLES.get(sector_key, sector_meta.get("sector_name", sector_key))
    watchlist_lines = [
        f"| {snapshot['name']} | {snapshot['ts_code']} | trend_strength={snapshot['trend_strength']:.0f}, pct_chg={(snapshot.get('pct_chg') or 0.0):.2f}% |"
        for snapshot in sector_targets
    ]
    us_rows = []
    for symbol in sector_meta.get("us_benchmarks", [])[:4]:
        matched = next((row for row in us_moves if row[0] == symbol), None)
        if matched:
            us_rows.append(f"| {matched[0]} | 景气映射 | {matched[1]:.2f}% |")

    source_bundle = build_source_bundle(
        build_base_local_sources(latest_ah, latest_us, latest_factor, summary_path),
        collect_supporting_sources(
            conn,
            entity_ids=[sector_key],
            allowed_types=["industry_research", "external_source_snapshot"],
            exclude_rel_paths={relative_to_project(card_path)},
        ),
    )
    if not source_bundle["gate_passed"]:
        draft_path = write_source_gate_draft(
            report_id=report_id,
            title=f"{sector_title} 主线趋势快照",
            created_at=created_at,
            reason="缺少可直接复核的本机支持来源，行业研究卡本轮只落草稿，不写入正式 research_index。",
            context_lines=[
                f"sector_key: {sector_key}",
                f"latest_ah_date: {latest_ah}",
                f"latest_us_date: {latest_us}",
                f"sector_target_count: {len(sector_targets)}",
            ],
            source_bundle=source_bundle,
        )
        return {
            "status": "draft_only",
            "card_path": None,
            "draft_path": draft_path,
            "source_bundle": source_bundle,
            "sources_path": None,
        }

    write_text(
        card_path,
        f"""---
report_id: {report_id}
report_type: industry
sector: {sector_key}
title: {sector_title} 主线趋势快照
created_at: {created_at}
status: active
---

# {sector_title} 主线趋势快照

## Thesis

当前 `{sector_key}` 是最近一轮 SMR 动态研究中最强的主线之一，已经形成“本地趋势强化 + 美股链条联动 + 研究持续跟进”的共振结构。

## Thesis Strength: strong

## Sector Lifecycle: growth

## Catalyst Timeline

### Near-term (1-4 weeks)
- 当前强势标的能否维持在 `MA20` 上方，并继续扩散到同板块更多公司。
- 对应美股基准能否继续维持正向联动。

### Mid-term (1-3 months)
- 订单、客户和收入兑现能否把主题交易推进到业绩交易。

### Long-term (3-12 months)
- 行业技术路线和龙头份额是否继续强化，决定估值中枢能否上移。

## US Linkage

| US Benchmark | Transmission Type | Latest Move |
|-------------|-------------------|-------------|
{chr(10).join(us_rows) if us_rows else '| - | - | - |'}

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| 估值扩张过快 | 中 | 高 | 结合订单与财报验证 |
| 美股映射转弱 | 中 | 高 | 跟踪对应 US benchmark |
| 主线拥挤交易 | 中 | 中 | 用分批而不是追高处理 |

## Thesis Breakers

1. 海外映射链条连续转弱，且本地标的无法独立维持趋势。
2. 板块核心标的集体跌回 `MA60` 下方，说明趋势一致性被破坏。
3. 深度研究后发现订单、客户或竞争格局不支持当前估值。

## Watchlist Additions

| Stock | Code | Reason |
|-------|------|--------|
{chr(10).join(watchlist_lines)}

{render_source_section(source_bundle)}

---

⚠️ 风险提示与免责声明

本内容仅供研究参考，不构成任何投资建议。股市有风险，投资需谨慎。
过往业绩不代表未来表现。请根据自身风险承受能力独立做出投资决策。
中长线趋势判断存在不确定性，市场可能长期偏离基本面逻辑。
作者及同行资本不对因参考本内容造成的任何投资损失承担责任。
""",
    )

    write_text(
        report_dir / "thesis.md",
        "\n".join(
            [
                "# Thesis",
                "",
                f"- {sector_title} 是最近一轮动态趋势筛选里最强的主线之一。",
                "- 当前入选对象来自最新因子和研究结论，而不是固定名单。",
                "- 后续要继续用订单、客户和竞争格局去验证这条主线是否值得维持优先级。",
            ]
        ),
    )

    write_text(
        report_dir / "catalyst.md",
        "\n".join(
            [
                "# Catalyst",
                "",
                f"- latest_ah_date: {latest_ah}",
                f"- latest_us_date: {latest_us}",
                "- 当前阶段以美股映射、强势股结构完整性和后续研究补证为主要催化。",
            ]
        ),
    )

    write_text(
        report_dir / "risk_assessment.md",
        "\n".join(
            [
                "# Risk Assessment",
                "",
                "- 若美股链条转弱，本地高估值标的波动会明显放大。",
                "- 若后续补证不支持当前估值，主线会从研究驱动切回纯情绪驱动。",
            ]
        ),
    )

    write_text(
        report_dir / "us_linkage.md",
        "\n".join(
            [
                "# US Linkage",
                "",
                "- 该行业卡优先跟踪 sector_config 中定义的 US benchmark。",
                "- 后续动态股票池会结合这些 benchmark 的温度去决定观察池扩张或收缩。",
            ]
        ),
    )

    write_text(
        report_dir / "conclusion.md",
        "\n".join(
            [
                "# Conclusion",
                "",
                f"- 结论：`{sector_key}` 是当前值得优先研究的动态主线之一。",
                "- 后续动作：继续生成个股卡，并交由动态池重建脚本决定入池/出池。",
            ]
        ),
    )

    sources_path = write_source_bundle_file(report_dir, source_bundle)

    conn.execute(
        """
        INSERT OR REPLACE INTO research_index
        (report_id, report_type, sector, title, ts_codes, created_at, file_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report_id,
            "industry",
            sector_key,
            f"{sector_title} 主线趋势快照",
            ",".join(snapshot["ts_code"] for snapshot in sector_targets),
            created_at,
            str(card_path),
        ),
    )
    return {
        "status": "generated",
        "card_path": card_path,
        "draft_path": None,
        "source_bundle": source_bundle,
        "sources_path": sources_path,
    }


def write_stock_pack(conn, created_at, latest_ah, latest_us, latest_factor, summary_path, snapshot, sector_meta, current_sector_card_path=None):
    ts_code = snapshot["ts_code"]
    report_id = f"{ts_code.lower().replace('.', '_')}_{snapshot['trade_date']}_initial_trend_card"
    report_dir = STOCK_DIR / ts_code / report_id
    card_path = report_dir / "00_research-card.md"

    us_refs = us_ref_list(snapshot, sector_meta)
    linkage_text = SECTOR_LINKAGE_TEXT.get(snapshot["sector"], "行业景气映射")
    direction = trend_direction(snapshot)
    valuation = valuation_assessment(snapshot)
    target_pool = suggested_pool(snapshot)
    research_snapshot = latest_external_research_snapshot(conn, ts_code)

    if target_pool == "candidate":
        pool_reason = "当前趋势清晰，已满足进入 `candidate` 的初筛条件，后续再用深度研究决定是否升级到 `recommended`。"
    else:
        pool_reason = "当前趋势开始改善，但还没到候选池强度，先保留在 `watchlist` 更合适。"

    thesis = (
        f"{snapshot['name']} 当前处在 `{snapshot['trend_strength']:.0f}` 分趋势区间，"
        f"价格位于 MA20/60/120 上方或附近，且受 {linkage_text} 支撑，"
        "适合作为 SMR 动态研究链路中的优先跟踪对象。"
    )

    supporting_sources = collect_supporting_sources(
        conn,
        entity_ids=[ts_code, snapshot["sector"]],
        allowed_types=["external_source_snapshot", "recommendation_card", "stock_research", "industry_research"],
        exclude_rel_paths={relative_to_project(card_path)},
    )
    if current_sector_card_path:
        supporting_sources.insert(
            0,
            supporting_bundle_source(
                source_type="industry_research_current_batch",
                title=f"{snapshot['sector']} 当前批次主线趋势卡",
                rel_path=relative_to_project(current_sector_card_path),
                source_path=str(current_sector_card_path),
                updated_at=created_at,
                entity_id=snapshot["sector"],
                detail="当前批次已生成并通过来源门禁的行业卡",
            ),
        )
    source_bundle = build_source_bundle(
        build_base_local_sources(latest_ah, latest_us, latest_factor, summary_path),
        supporting_sources[:8],
    )
    if not source_bundle["gate_passed"]:
        draft_path = write_source_gate_draft(
            report_id=report_id,
            title=f"{snapshot['name']} 初始趋势研究卡",
            created_at=created_at,
            reason="缺少可直接复核的本机支持来源，个股研究卡本轮只落草稿，不写入正式 research_index。",
            context_lines=[
                f"ts_code: {ts_code}",
                f"sector: {snapshot['sector']}",
                f"trend_strength: {snapshot.get('trend_strength', 'N/A')}",
                f"latest_close: {snapshot.get('close', 'N/A')}",
                f"suggested_pool: {target_pool}",
            ],
            source_bundle=source_bundle,
        )
        return {
            "status": "draft_only",
            "card_path": None,
            "draft_path": draft_path,
            "source_bundle": source_bundle,
            "sources_path": None,
        }

    write_text(
        card_path,
        f"""---
report_id: {report_id}
report_type: stock
sector: {snapshot['sector']}
ts_code: {ts_code}
title: {snapshot['name']} 初始趋势研究卡
created_at: {created_at}
status: active
---

# {snapshot['name']} 初始趋势研究卡

## Thesis

{thesis}

## Sector Thesis Link

该标的属于 `{snapshot['sector']}` 动态主线，当前入选来自最新因子排名，而不是固定手工名单。

## Competitive Position: leading_watchlist

## Valuation Assessment: {valuation}

## Key Financials

| Metric | Latest | Trend |
|--------|--------|-------|
| ROE_est | {snapshot.get('roe_est', 'N/A')} | 轻量快照 |
| PE_TTM | {snapshot.get('pe_ttm', 'N/A')} | 当前估值快照 |
| PB | {snapshot.get('pb', 'N/A')} | 当前估值快照 |
| Market Cap (CNY 1e8) | {snapshot.get('market_cap', 'N/A')} | 当前快照 |

{render_external_research_section(research_snapshot)}

## US Linkage

| US Benchmark | Link Type | Impact |
|-------------|-----------|--------|
| {' / '.join(us_refs) if us_refs else '-'} | {linkage_text} | 当前外部环境 {'偏正面' if us_refs else '待补映射'} |

## Key Risks

1. 高估值主线里，趋势一旦转弱，回撤会被放大。
2. 当前卡片仍以行情和轻量基本面快照为主，后续需要补客户、订单和竞争格局。
3. 若对应美股链条明显转弱，本地映射逻辑会先失效。

## Thesis Breakers

1. 股价持续跌回 `MA60` 下方，趋势结构被破坏。
2. 后续深度研究发现订单、客户或竞争位置不支持当前逻辑。
3. 对应海外映射明显转弱，且本地标的未表现出独立性。

## Suggested Pool: {target_pool}

Reasoning: {pool_reason}

{render_source_section(source_bundle)}

---

⚠️ 风险提示与免责声明

本内容仅供研究参考，不构成任何投资建议。股市有风险，投资需谨慎。
过往业绩不代表未来表现。请根据自身风险承受能力独立做出投资决策。
中长线趋势判断存在不确定性，市场可能长期偏离基本面逻辑。
作者及同行资本不对因参考本内容造成的任何投资损失承担责任。
""",
    )

    us_link_lines = [
        f"- {symbol} linkage={value:.2f}" for symbol, value in sorted(snapshot.get("us_links", {}).items(), key=lambda item: item[1], reverse=True)
    ]
    write_text(
        report_dir / "thesis.md",
        "\n".join(
            [
                "# Thesis",
                "",
                f"- {snapshot['name']} 当前价格 {snapshot['close']:.2f}，位于 MA20 {snapshot.get('ma_20', 0):.2f}、MA60 {snapshot.get('ma_60', 0):.2f}、MA120 {snapshot.get('ma_120', 0):.2f} 附近。",
                f"- latest pct_chg: {(snapshot.get('pct_chg') or 0.0):.2f}%，trend_strength={snapshot.get('trend_strength', 0):.0f}。",
                "- 当前入选逻辑来自动态排序，不依赖手工指定股票名单。",
            ]
        ),
    )

    write_text(
        report_dir / "valuation.md",
        "\n".join(
            [
                "# Valuation",
                "",
                f"- PE_TTM: {snapshot.get('pe_ttm', 'N/A')}",
                f"- PB: {snapshot.get('pb', 'N/A')}",
                f"- ROE_est: {snapshot.get('roe_est', 'N/A')}",
                f"- Market Cap (CNY 1e8): {snapshot.get('market_cap', 'N/A')}",
                "",
                render_external_research_section(research_snapshot).strip(),
                "",
                "- 结论：当前更适合结合趋势、景气和后续研究补证来判断，而不是只看静态估值。",
            ]
        ),
    )

    write_text(
        report_dir / "us_linkage.md",
        "\n".join(["# US Linkage", "", f"- linkage_path: {linkage_text}"] + us_link_lines),
    )

    write_text(
        report_dir / "risk_assessment.md",
        "\n".join(
            [
                "# Risk Assessment",
                "",
                "- 动态强势股通常同时伴随高波动和高估值。",
                "- 后续需要继续用深度研究来判断它是持续主线，还是短期情绪扩散。",
            ]
        ),
    )

    write_text(
        report_dir / "conclusion.md",
        "\n".join(
            [
                "# Conclusion",
                "",
                f"- trend_direction: {direction}",
                f"- suggested_pool: {target_pool}",
                "- 下一步：交给动态池重建脚本同步当前池状态，并补深度研究判断是否升级。",
            ]
        ),
    )

    sources_path = write_source_bundle_file(report_dir, source_bundle)

    conn.execute(
        """
        INSERT OR REPLACE INTO research_index
        (report_id, report_type, sector, title, ts_codes, created_at, file_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report_id,
            "stock",
            snapshot["sector"],
            f"{snapshot['name']} 初始趋势研究卡",
            ts_code,
            created_at,
            str(card_path),
        ),
    )
    return {
        "status": "generated",
        "card_path": card_path,
        "draft_path": None,
        "source_bundle": source_bundle,
        "sources_path": sources_path,
    }


def main():
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    registry_meta = load_active_equity_universe(conn, include_seed=True)
    sector_meta = sector_config(conn)
    latest_ah, latest_us, latest_factor = latest_dates(conn)
    snapshots = load_snapshots(conn, registry_meta, latest_ah, latest_factor)
    targets = select_targets(snapshots)
    if not targets:
        raise SystemExit("No dynamic targets matched the current trend threshold")

    us_moves = latest_us_moves(conn)
    summary_path = write_factor_summary(created_at, latest_ah, latest_us, targets, us_moves)

    top_sector = dominant_sector(targets)
    industry_result = write_industry_pack(
        conn,
        created_at,
        latest_ah,
        latest_us,
        latest_factor,
        summary_path,
        targets,
        us_moves,
        top_sector,
        sector_meta.get(top_sector, {"sector_name": top_sector, "us_benchmarks": []}),
    )
    industry_card_path = industry_result["card_path"] or industry_result["draft_path"]

    stock_results = [
        write_stock_pack(
            conn,
            created_at,
            latest_ah,
            latest_us,
            latest_factor,
            summary_path,
            snapshot,
            sector_meta.get(snapshot["sector"], {"us_benchmarks": []}),
            current_sector_card_path=industry_result["card_path"] if snapshot["sector"] == top_sector else None,
        )
        for snapshot in targets
    ]
    stock_cards = [item["card_path"] for item in stock_results if item["card_path"]]
    draft_cards = [item["draft_path"] for item in [industry_result, *stock_results] if item["draft_path"]]
    generated_card_count = len(stock_cards) + (1 if industry_result["card_path"] else 0)

    registry_entry = register_snapshot(
        conn,
        entity_type="trend_research_batch",
        entity_id=latest_ah,
        status="generated" if generated_card_count else "draft_only",
        source="generate_trend_batch.py",
        relationships={
            "latest_us_date": latest_us,
            "latest_factor_date": latest_factor,
            "top_sector": top_sector,
        },
        payload={
            "created_at": created_at,
            "target_count": len(targets),
            "target_ts_codes": [snapshot["ts_code"] for snapshot in targets],
            "target_sectors": sorted({snapshot["sector"] for snapshot in targets}),
            "summary_rel_path": relative_to_project(summary_path),
            "industry_card_rel_path": relative_to_project(industry_result["card_path"]) if industry_result["card_path"] else None,
            "industry_draft_rel_path": relative_to_project(industry_result["draft_path"]) if industry_result["draft_path"] else None,
            "stock_card_rel_paths": [relative_to_project(path) for path in stock_cards],
            "draft_rel_paths": [relative_to_project(path) for path in draft_cards],
            "generated_card_count": generated_card_count,
            "draft_card_count": len(draft_cards),
        },
        created_at=created_at,
    )
    if generated_card_count:
        handoff_result = ensure_auto_handoff(
            conn,
            registry_entry,
            note="趋势研究批次已生成，自动转交 Hermes-like 研究代理压缩上下文。",
            created_by="generate_trend_batch.py",
        )
    else:
        handoff_result = {"reason": "skipped_no_formal_cards", "handoff": None}
    conn.commit()
    conn.close()

    log_run(
        "generate_trend_batch.py",
        "success" if generated_card_count else "warning",
        "dynamic trend research generated",
        {
            "target_count": len(targets),
            "top_sector": top_sector,
            "summary_path": str(summary_path),
            "industry_card_path": str(industry_card_path),
            "generated_card_count": generated_card_count,
            "draft_card_count": len(draft_cards),
            "draft_paths": [str(path) for path in draft_cards],
            "handoff_result": handoff_result["reason"],
            "handoff_id": handoff_result["handoff"]["handoff_id"] if handoff_result["handoff"] else None,
        },
    )
    print(f"Trend summary: {summary_path}")
    if industry_result["card_path"]:
        print(f"Industry card: {industry_result['card_path']}")
    if industry_result["draft_path"]:
        print(f"Industry draft: {industry_result['draft_path']}")
    for path in stock_cards:
        print(f"Stock card: {path}")
    for path in draft_cards:
        if path != industry_result["draft_path"]:
            print(f"Stock draft: {path}")
    if handoff_result["handoff"]:
        print(
            f"Auto handoff {handoff_result['reason']}: "
            f"{handoff_result['handoff']['handoff_id']} -> {handoff_result['handoff']['to_profile_id']}"
        )
    else:
        print(f"Auto handoff skipped: {handoff_result['reason']}")


if __name__ == "__main__":
    main()
