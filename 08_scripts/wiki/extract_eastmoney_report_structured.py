#!/usr/bin/env python3
"""Build structured Eastmoney report snapshots from article/pdf-text sources."""

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_external_sources import persist_external_snapshot, truncate_text
from smr_paths import env_or_project_path, project_path
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import resolve_equity_targets
from smr_wiki import slugify

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")

SECTION_ALIASES = {
    "事件": "event",
    "投资要点": "investment_points",
    "盈利预测": "forecast",
    "盈利预期": "forecast",
    "风险提示": "risks",
    "投资建议": "recommendation",
}
KEYWORD_CANDIDATES = [
    "AI",
    "800G",
    "1.6T",
    "CPO",
    "NPO",
    "OCS",
    "AEC",
    "硅光",
    "光引擎",
    "海外",
    "泰国",
    "H股",
    "算力",
    "产能",
]


def normalize_text(text):
    return " ".join(str(text or "").split())


def slug_source_id(provider, ts_code, info_code):
    stable_key = f"{ts_code}_{info_code}"
    return f"external_source__{slugify(provider)}__{slugify(stable_key)[:120]}"


def snapshot_exists_on_disk(ts_code, info_code, source_kind):
    entity_dir = project_path("11_smr_wiki", "raw", "external", "stock", slugify(ts_code))
    if not entity_dir.exists():
        return False
    pattern = f"*/{slugify(info_code)}__{slugify(source_kind)}__*.meta.json"
    return any(entity_dir.glob(pattern))


def snapshot_exists(conn, ts_code, info_code, provider, source_kind):
    row = conn.execute(
        """
        SELECT 1
        FROM source_manifest
        WHERE source_type='external_source_snapshot'
          AND entity_id=?
          AND source_id=?
        LIMIT 1
        """,
        (ts_code, slug_source_id(provider, ts_code, info_code)),
    ).fetchone()
    if row is not None:
        return True
    return snapshot_exists_on_disk(ts_code, info_code, source_kind)


def resolve_targets(conn, args):
    return resolve_equity_targets(
        conn,
        explicit_ts_codes=args.ts_code,
        profile_name=args.profile,
        pool_types=args.pool_type,
        allowed_markets=["SZ", "SH", "BJ"],
        limit=args.limit,
    )


def query_external_rows(conn, ts_code, source_kind, limit):
    rows = conn.execute(
        """
        SELECT source_rel_path, metadata_json, created_at, updated_at
        FROM source_manifest
        WHERE source_type='external_source_snapshot'
          AND entity_id=?
          AND json_extract(metadata_json, '$.source_kind')=?
        ORDER BY datetime(updated_at) DESC, datetime(created_at) DESC, source_id DESC
        LIMIT ?
        """,
        (ts_code, source_kind, limit),
    ).fetchall()
    results = []
    for source_rel_path, metadata_json, created_at, updated_at in rows:
        manifest_meta = json.loads(metadata_json or "{}")
        meta_rel_path = manifest_meta.get("meta_rel_path")
        if not meta_rel_path:
            continue
        meta_path = project_path(meta_rel_path)
        source_path = project_path(source_rel_path)
        if (not meta_path.exists()) or (not source_path.exists()):
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["_meta_rel_path"] = meta_rel_path
        meta["_source_rel_path"] = source_rel_path
        meta["_created_at"] = created_at
        meta["_updated_at"] = updated_at
        results.append(meta)
    return results


def parse_article_markdown(path):
    text = path.read_text(encoding="utf-8")
    marker = "正文："
    if marker not in text:
        return ""
    body = text.split(marker, 1)[1]
    return body.strip()


def split_paragraphs(text):
    paragraphs = []
    for chunk in re.split(r"\n\s*\n", str(text or "").strip()):
        cleaned = normalize_text(chunk)
        if cleaned:
            paragraphs.append(cleaned)
    return paragraphs


def normalize_heading(text):
    return normalize_text(re.sub(r"[：:]+$", "", str(text or "")))


def parse_sections(body_text):
    paragraphs = split_paragraphs(body_text)
    sections = {}
    current_key = "body"
    current_paragraphs = []

    def flush():
        nonlocal current_paragraphs
        if current_paragraphs:
            existing = sections.get(current_key)
            merged = "\n\n".join(current_paragraphs)
            sections[current_key] = f"{existing}\n\n{merged}".strip() if existing else merged
            current_paragraphs = []

    for paragraph in paragraphs:
        alias = None
        inline_rest = ""
        heading = normalize_heading(paragraph)
        if heading in SECTION_ALIASES:
            alias = SECTION_ALIASES[heading]
        else:
            for raw_heading, mapped_alias in SECTION_ALIASES.items():
                for marker in (f"{raw_heading}：", f"{raw_heading}:"):
                    if paragraph.startswith(marker):
                        alias = mapped_alias
                        inline_rest = normalize_text(paragraph[len(marker) :])
                        break
                if alias:
                    break

        if alias:
            flush()
            current_key = alias
            if inline_rest:
                current_paragraphs.append(inline_rest)
            continue
        current_paragraphs.append(paragraph)
    flush()
    return sections


def extract_values(value_text):
    return [float(token) for token in re.findall(r"[-+]?\d+(?:\.\d+)?", value_text or "")]


def year_labels(start_year, end_year):
    if not start_year or not end_year:
        return []
    start = int(start_year)
    end = int(end_year)
    if end < start:
        return []
    return [str(year) for year in range(start, end + 1)]


def map_year_values(years, values):
    if not years or not values:
        return {}
    if len(values) < len(years):
        return {}
    return {year: value for year, value in zip(years, values[: len(years)])}


def parse_target_price(text):
    match = re.search(r"目标价[^\d]{0,8}([0-9]+(?:\.[0-9]+)?)", text or "")
    if not match:
        return None
    return float(match.group(1))


def parse_forecast_metrics(forecast_text, search_item):
    result = {
        "revenue_billion": {},
        "net_profit_billion": {},
        "eps_yuan": {},
        "pe_multiple": {},
        "yoy_percent": {},
        "target_price_yuan": None,
        "raw_search_item_forecast": {},
    }
    text = normalize_text(forecast_text)

    revenue_match = re.search(
        r"(20\d{2})-(20\d{2})年(?:收入|营收|营业收入)分别为([^。；]+)",
        text,
    )
    if revenue_match:
        years = year_labels(revenue_match.group(1), revenue_match.group(2))
        values = extract_values(revenue_match.group(3))
        result["revenue_billion"] = map_year_values(years, values)

    net_profit_match = re.search(
        r"(20\d{2})-(20\d{2})年(?:归母净利|归母净利润|净利润)分别为([^。；]+)",
        text,
    )
    if net_profit_match:
        years = year_labels(net_profit_match.group(1), net_profit_match.group(2))
        values = extract_values(net_profit_match.group(3))
        result["net_profit_billion"] = map_year_values(years, values)

    net_profit_upgrade_match = re.search(
        r"将(20\d{2})-(20\d{2})年(?:的)?归母净利(?:润)?从[^，。]+上调至([0-9\./、，]+)亿[^，。]*，预计(20\d{2})年归母净利(?:润)?为([0-9\./、，]+)",
        text,
    )
    if net_profit_upgrade_match:
        first_years = year_labels(net_profit_upgrade_match.group(1), net_profit_upgrade_match.group(2))
        first_values = extract_values(net_profit_upgrade_match.group(3))
        upgraded = map_year_values(first_years, first_values)
        tail_values = extract_values(net_profit_upgrade_match.group(5))
        if tail_values:
            upgraded[net_profit_upgrade_match.group(4)] = tail_values[0]
        if upgraded:
            result["net_profit_billion"] = upgraded

    yoy_match = re.search(r"YOY分别为([+\-0-9\./%、，]+)", text)
    if yoy_match and result["net_profit_billion"]:
        years = list(result["net_profit_billion"].keys())
        values = extract_values(yoy_match.group(1))
        result["yoy_percent"] = map_year_values(years, values)

    eps_match = re.search(r"EPS分别为([0-9\./、，]+)元", text)
    if eps_match:
        values = extract_values(eps_match.group(1))
        years = list(result["net_profit_billion"].keys()) or list(result["revenue_billion"].keys())
        if len(values) == len(years):
            result["eps_yuan"] = map_year_values(years, values)
        else:
            eps_year_match = re.search(r"(20\d{2})-(20\d{2})年.*?EPS分别为([0-9\./、，]+)元", text)
            if eps_year_match:
                eps_years = year_labels(eps_year_match.group(1), eps_year_match.group(2))
                result["eps_yuan"] = map_year_values(eps_years, values)

    pe_match = re.search(r"(20\d{2})-(20\d{2})年P/?E为([0-9\./、，]+)倍", text)
    if not pe_match:
        pe_match = re.search(r"PE分别为([0-9\./、，]+)倍", text)
        if pe_match:
            years = list(result["eps_yuan"].keys()) or list(result["net_profit_billion"].keys()) or list(result["revenue_billion"].keys())
            values = extract_values(pe_match.group(1))
            result["pe_multiple"] = map_year_values(years, values)
    else:
        pe_years = year_labels(pe_match.group(1), pe_match.group(2))
        pe_values = extract_values(pe_match.group(3))
        result["pe_multiple"] = map_year_values(pe_years, pe_values)

    result["target_price_yuan"] = parse_target_price(text)
    if result["target_price_yuan"] is None:
        for key in ("indvAimPriceT", "indvAimPriceL"):
            value = search_item.get(key)
            if value not in (None, ""):
                try:
                    result["target_price_yuan"] = float(value)
                    break
                except ValueError:
                    pass

    for key in (
        "predictThisYearEps",
        "predictNextYearEps",
        "predictNextTwoYearEps",
        "predictThisYearPe",
        "predictNextYearPe",
        "predictNextTwoYearPe",
        "indvAimPriceT",
        "indvAimPriceL",
        "emRatingName",
        "sRatingName",
    ):
        if search_item.get(key) not in (None, ""):
            result["raw_search_item_forecast"][key] = search_item.get(key)

    return result


def build_risk_items(risk_text):
    if not risk_text:
        return []
    text = normalize_text(re.sub(r"^风险提示[：:]\s*", "", risk_text))
    text = re.sub(r"^[0-9]+[、.]", "", text)
    parts = re.split(r"[；;。]", text)
    items = []
    for part in parts:
        cleaned = normalize_text(re.sub(r"^[0-9]+[、.,，]\s*", "", part.strip("，, ")))
        if len(cleaned) >= 4:
            items.append(cleaned)
    return items


def detect_keywords(*texts):
    merged = "\n".join(str(text or "") for text in texts)
    hits = []
    for keyword in KEYWORD_CANDIDATES:
        if keyword.lower() in merged.lower():
            hits.append(keyword)
    return hits


def build_structured_payload(target, article_meta, sections, forecast_metrics, pdf_text_meta):
    search_item = article_meta.get("search_item") or {}
    researchers = [value.strip() for value in re.split(r"[,，/]", article_meta.get("researcher") or "") if value.strip()]
    payload = {
        "schema_version": "smr_report_structured_v1",
        "provider": "eastmoney_report_structured",
        "document": {
            "info_code": article_meta.get("info_code"),
            "ts_code": target["ts_code"],
            "stock_name": target["name"],
            "title": search_item.get("title") or article_meta.get("title") or "",
            "published_at": article_meta.get("published_at") or "",
            "org_name": article_meta.get("org_name") or "",
            "researchers": researchers,
            "rating_name": article_meta.get("rating_name") or "",
            "market": search_item.get("market") or "",
            "industry_name": search_item.get("indvInduName") or search_item.get("industryName") or "",
        },
        "summary": article_meta.get("summary") or "",
        "sections": sections,
        "forecast_metrics": forecast_metrics,
        "risk_items": build_risk_items(sections.get("risks", "")),
        "keywords": detect_keywords(
            article_meta.get("summary"),
            sections.get("body"),
            sections.get("event"),
            sections.get("investment_points"),
            sections.get("forecast"),
            pdf_text_meta.get("_raw_text", ""),
        ),
        "source_refs": {
            "article_markdown_rel_path": article_meta.get("_source_rel_path"),
            "article_meta_rel_path": article_meta.get("_meta_rel_path"),
            "pdf_text_markdown_rel_path": pdf_text_meta.get("_source_rel_path"),
            "pdf_text_meta_rel_path": pdf_text_meta.get("_meta_rel_path"),
            "pdf_text_raw_rel_path": pdf_text_meta.get("_raw_rel_path"),
            "detail_url": article_meta.get("source_url") or article_meta.get("requested_url") or "",
            "pdf_url": pdf_text_meta.get("source_url") or article_meta.get("attach_url") or "",
        },
        "llm_blocks": [
            {"type": "summary", "text": article_meta.get("summary") or ""},
            {"type": "section", "name": "event", "text": sections.get("event", "")},
            {"type": "section", "name": "investment_points", "text": sections.get("investment_points", "")},
            {"type": "section", "name": "forecast", "text": sections.get("forecast", "")},
            {"type": "section", "name": "risks", "text": sections.get("risks", "")},
        ],
    }
    return payload


def build_body_text(payload):
    doc = payload["document"]
    forecast = payload["forecast_metrics"]
    lines = [
        f"证券代码：{doc['ts_code']}",
        f"证券简称：{doc['stock_name']}",
        f"研报编号：{doc['info_code']}",
        f"报告标题：{doc['title']}",
        f"发布时间：{doc['published_at'] or '-'}",
        f"发布机构：{doc['org_name'] or '-'}",
        f"研究员：{', '.join(doc['researchers']) or '-'}",
        f"投资评级：{doc['rating_name'] or '-'}",
        f"行业：{doc['industry_name'] or '-'}",
    ]
    if forecast.get("target_price_yuan") is not None:
        lines.append(f"目标价：{forecast['target_price_yuan']}")
    if payload["keywords"]:
        lines.append(f"关键词：{', '.join(payload['keywords'])}")
    lines.append("")
    if payload["summary"]:
        lines.extend(["摘要：", payload["summary"], ""])
    if forecast["revenue_billion"]:
        lines.append(f"营收预测(亿元)：{json.dumps(forecast['revenue_billion'], ensure_ascii=False)}")
    if forecast["net_profit_billion"]:
        lines.append(f"净利润预测(亿元)：{json.dumps(forecast['net_profit_billion'], ensure_ascii=False)}")
    if forecast["eps_yuan"]:
        lines.append(f"EPS预测(元)：{json.dumps(forecast['eps_yuan'], ensure_ascii=False)}")
    if forecast["pe_multiple"]:
        lines.append(f"PE预测(倍)：{json.dumps(forecast['pe_multiple'], ensure_ascii=False)}")
    if payload["risk_items"]:
        lines.extend(["", "风险提示：", "；".join(payload["risk_items"])])
    if payload["sections"].get("investment_points"):
        lines.extend(["", "投资要点：", truncate_text(payload["sections"]["investment_points"], limit=2500)])
    if payload["sections"].get("forecast"):
        lines.extend(["", "盈利预测原文：", truncate_text(payload["sections"]["forecast"], limit=2000)])
    return truncate_text("\n".join(lines), limit=12000)


def persist_structured_snapshot(target, article_meta, payload, fetched_at):
    info_code = article_meta["info_code"]
    published_at = normalize_text(article_meta.get("published_at"))
    bucket_date = (published_at[:10] if published_at else fetched_at[:10]) or fetched_at[:10]
    title = f"{target['ts_code']} 东方财富研报结构化 {payload['document']['title'] or info_code}"
    raw_bytes = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return persist_external_snapshot(
        title=title,
        fetched_at=fetched_at,
        entity_type="stock",
        entity_id=target["ts_code"],
        source_kind="research_structured",
        source_url=payload["source_refs"]["detail_url"] or payload["source_refs"]["pdf_url"],
        source_domain="data.eastmoney.com",
        content_type="application/json",
        raw_bytes=raw_bytes,
        raw_extension=".json",
        note=f"structured eastmoney report payload for {target['name']}",
        tags=["eastmoney", "public_research", "report_structured"],
        body_text=build_body_text(payload),
        metadata={
            "info_code": info_code,
            "published_at": published_at,
            "org_name": payload["document"]["org_name"],
            "researchers": payload["document"]["researchers"],
            "rating_name": payload["document"]["rating_name"],
            "industry_name": payload["document"]["industry_name"],
            "keywords": payload["keywords"],
            "source_refs": payload["source_refs"],
        },
        extra_frontmatter={
            "provider": "eastmoney_report_structured",
            "announcement_id": f"{target['ts_code']}_{info_code}",
            "published_at": published_at,
            "org_name": payload["document"]["org_name"],
            "researcher": ",".join(payload["document"]["researchers"]),
            "rating_name": payload["document"]["rating_name"],
            "info_code": info_code,
        },
        stable_key=info_code,
        bucket_date=bucket_date,
    )


def load_pdf_text_map(conn, ts_code, limit):
    rows = query_external_rows(conn, ts_code, "research_pdf_text", limit)
    mapping = {}
    for meta in rows:
        info_code = meta.get("info_code")
        if not info_code:
            continue
        raw_rel_path = meta.get("_raw_rel_path")
        if not raw_rel_path:
            raw_rel_path = meta.get("raw_rel_path")
        raw_text = ""
        if raw_rel_path:
            raw_path = project_path(raw_rel_path)
            if raw_path.exists():
                raw_text = raw_path.read_text(encoding="utf-8")
        meta["_raw_text"] = raw_text
        meta["_raw_rel_path"] = raw_rel_path
        mapping[info_code] = meta
    return mapping


def main():
    parser = argparse.ArgumentParser(description="Build structured Eastmoney report snapshots from existing article/pdf-text sources")
    parser.add_argument("--ts-code", action="append", help="Specific A-share ts_code; can be repeated")
    parser.add_argument("--profile", default="standard_external", help="Coverage profile from research_amplification_registry.md")
    parser.add_argument("--pool-type", action="append", help="Override pool type; can be repeated")
    parser.add_argument("--limit", type=int, help="Override maximum number of target symbols")
    parser.add_argument("--report-limit", type=int, default=2, help="Maximum structured reports to build for each symbol")
    parser.add_argument("--force", action="store_true", help="Build even if the structured snapshot already exists")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    targets = resolve_targets(conn, args)
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    persisted = []
    skipped = []
    empty = []
    failed = []

    for target in targets:
        article_rows = query_external_rows(conn, target["ts_code"], "research_article", args.report_limit)
        if not article_rows:
            empty.append({"ts_code": target["ts_code"], "reason": "missing_research_article_snapshot"})
            continue
        pdf_text_map = load_pdf_text_map(conn, target["ts_code"], args.report_limit * 3)

        for article_meta in article_rows:
            info_code = article_meta.get("info_code") or ""
            if not info_code:
                failed.append({"ts_code": target["ts_code"], "error": "missing_info_code"})
                continue
            if (not args.force) and snapshot_exists(
                conn,
                target["ts_code"],
                info_code,
                provider="eastmoney_report_structured",
                source_kind="research_structured",
            ):
                skipped.append({"ts_code": target["ts_code"], "info_code": info_code, "reason": "already_exists"})
                continue
            try:
                article_path = project_path(article_meta["_source_rel_path"])
                body_text = parse_article_markdown(article_path)
                sections = parse_sections(body_text)
                pdf_text_meta = pdf_text_map.get(info_code, {})
                forecast_text = sections.get("forecast", "")
                forecast_metrics = parse_forecast_metrics(forecast_text, article_meta.get("search_item") or {})
                payload = build_structured_payload(target, article_meta, sections, forecast_metrics, pdf_text_meta)
                snapshot = persist_structured_snapshot(target, article_meta, payload, fetched_at)
                persisted.append(
                    {
                        "ts_code": target["ts_code"],
                        "info_code": info_code,
                        "title": snapshot["title"],
                        "markdown_rel_path": snapshot["markdown_rel_path"],
                        "raw_rel_path": snapshot["raw_rel_path"],
                    }
                )
            except Exception as exc:
                failed.append({"ts_code": target["ts_code"], "info_code": info_code, "error": str(exc)})

    register_snapshot(
        conn,
        entity_type="eastmoney_report_structured_batch",
        entity_id=datetime.now().strftime("%Y-%m-%d"),
        status="fetched" if persisted else "empty",
        source="extract_eastmoney_report_structured.py",
        relationships={
            "target_count": len(targets),
            "profile": args.profile,
            "requested_pool_types": args.pool_type or [],
            "limit": args.limit,
            "report_limit": args.report_limit,
            "force": args.force,
        },
        payload={
            "persisted_count": len(persisted),
            "skipped_count": len(skipped),
            "empty_count": len(empty),
            "failed_count": len(failed),
            "persisted": persisted[:20],
            "skipped": skipped[:20],
            "empty": empty[:20],
            "failed": failed[:20],
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "extract_eastmoney_report_structured.py",
        "success" if not failed else "warning",
        "eastmoney report structured snapshots built",
        {
            "target_count": len(targets),
            "profile": args.profile,
            "requested_pool_types": args.pool_type or [],
            "limit": args.limit,
            "report_limit": args.report_limit,
            "persisted_count": len(persisted),
            "skipped_count": len(skipped),
            "empty_count": len(empty),
            "failed_count": len(failed),
            "persisted": persisted[:20],
            "skipped": skipped[:20],
            "empty": empty[:20],
            "failed": failed[:20],
        },
    )

    print(f"Eastmoney report structured snapshots: {len(persisted)}")
    for item in persisted[:20]:
        print(f"- {item['ts_code']} | {item['info_code']} -> {item['markdown_rel_path']}")
    if skipped:
        print("Skipped:")
        for item in skipped[:20]:
            print(f"- {item['ts_code']} | {item['info_code']}: {item['reason']}")
    if empty:
        print("Empty:")
        for item in empty[:20]:
            print(f"- {item['ts_code']}: {item['reason']}")
    if failed:
        print("Failures:")
        for item in failed[:20]:
            print(f"- {item['ts_code']} | {item.get('info_code', '-')}: {item['error']}")


if __name__ == "__main__":
    main()
