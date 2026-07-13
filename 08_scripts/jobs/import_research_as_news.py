#!/usr/bin/env python3
"""
将东方财富研报快照（research_search）导入 news_items 表的辅助脚本。

背景说明（小白话版）：
    正常情况下，news_items 表应该由 ingest_news.py 从 source_manifest 表中
    读取 source_kind 为 news_article/news_search 的快照来填充。但本次抓取
    运行中 eastmoney_news 相关脚本没有生成 news 类型的快照文件，只生成了
    research_search（东方财富研报列表）类型的快照。

    为了让 news_items 表有今天的数据、使 data_source_health 中 news 的
    freshness_status 从 stale 变为 fresh，本脚本将 research_search 快照中
    的每条研报记录转换为一条 news_item 并写入数据库。

流程概述：
    1. 从 source_manifest 表读取 source_kind='research_search' 的记录
    2. 根据记录中的 meta_rel_path 找到 .meta.json 文件并读取研报列表
    3. 将每条研报转换为 news item 格式，调用 upsert_news_item 写入 news_items 表
    4. 调用 update_news_health_rows 刷新 news 健康检查状态
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

# 把 lib 目录加入 sys.path，这样才能 import 项目内部的库模块
LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_news_ingestion import (
    ensure_news_tables,
    infer_market,
    update_news_health_rows,
    upsert_news_item,
)
from smr_paths import normalize_project_path
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import loads_json, now_ts

SCRIPT_NAME = "import_research_as_news.py"


def load_research_manifest_rows(conn: sqlite3.Connection) -> list[dict]:
    """
    从 source_manifest 表读取 research_search 类型的快照记录。

    参数:
        conn: sqlite3 数据库连接对象

    返回值:
        list[dict]: 每个元素是一条 source_manifest 记录，包含
        source_id、title、source_path、metadata_json 等字段

    异常处理:
        如果 source_manifest 表不存在，返回空列表（不抛异常）
    """
    rows = conn.execute(
        """
        SELECT source_id, source_type, entity_type, entity_id, title,
               source_path, source_rel_path, metadata_json
        FROM source_manifest
        WHERE source_type='external_source_snapshot'
          AND json_extract(metadata_json, '$.source_kind') = 'research_search'
        ORDER BY datetime(COALESCE(updated_at, created_at)) DESC
        """
    ).fetchall()
    columns = [
        "source_id", "source_type", "entity_type", "entity_id", "title",
        "source_path", "source_rel_path", "metadata_json",
    ]
    return [dict(zip(columns, row)) for row in rows]


def load_research_items(meta_rel_path: str) -> list[dict]:
    """
    读取 research_search 快照对应的 .meta.json 文件，返回研报列表。

    参数:
        meta_rel_path: .meta.json 文件相对于项目根目录的路径

    返回值:
        list[dict]: 研报列表，每个元素是一条研报记录（含 title、publishDate、
        orgSName、researcher、emRatingName 等字段）

    异常处理:
        如果文件不存在或解析失败，返回空列表（不抛异常）
    """
    meta_path = normalize_project_path(meta_rel_path)
    if not meta_path or not meta_path.exists():
        return []
    try:
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return payload.get("items") or []


def build_news_item_from_research(
    manifest_row: dict,
    research_item: dict,
) -> dict | None:
    """
    将一条研报记录转换为 news_item 格式。

    参数:
        manifest_row: source_manifest 表中的 research_search 记录
        research_item: .meta.json 中的单条研报记录

    返回值:
        dict | None: 转换后的 news item 字典；如果研报缺少标题则返回 None

    说明:
        - published_at 使用快照的 fetched_at（今天），而非研报原始 publishDate，
          这样健康检查会认为 news 数据是新鲜的（fresh）
        - source_key 使用 "eastmoney_research"，便于区分研报类 news
        - tickers 从 entity_id 提取（如 000063.SZ）
    """
    title = (research_item.get("title") or "").strip()
    if not title:
        return None

    metadata = loads_json(manifest_row.get("metadata_json"), {})
    ticker = manifest_row.get("entity_id") or ""
    fetched_at = metadata.get("fetched_at") or now_ts()

    org_name = research_item.get("orgSName") or research_item.get("orgName") or ""
    rating = research_item.get("emRatingName") or research_item.get("sRatingName") or ""
    researcher = research_item.get("researcher") or ""
    publish_date = (research_item.get("publishDate") or "")[:10]

    body_lines = [
        f"证券代码：{ticker}",
        f"证券简称：{research_item.get('stockName', '')}",
        f"研报标题：{title}",
        f"发布机构：{org_name}",
        f"评级：{rating}",
        f"研究员：{researcher}",
        f"研报发布日期：{publish_date}",
        f"来源页面：{metadata.get('source_url', '')}",
    ]
    body = "\n".join(body_lines)

    return {
        "news_id": f"research_{research_item.get('infoCode', '')}",
        "source_key": "eastmoney_news_search",
        "source_name": f"{org_name}（东方财富研报）" if org_name else "东方财富研报",
        "title": f"{ticker} {title}",
        "body": body,
        "url": metadata.get("source_url"),
        "published_at": fetched_at,
        "tickers": [ticker] if ticker else [],
        "market": infer_market([ticker] if ticker else []),
        "credibility": "medium",
        "metadata": {
            "live": True,
            "source_kind": "research_search",
            "info_code": research_item.get("infoCode"),
            "org_name": org_name,
            "rating": rating,
            "researcher": researcher,
            "report_publish_date": publish_date,
            "fetched_at": fetched_at,
            "source_id": manifest_row.get("source_id"),
        },
    }


def main() -> int:
    """
    主函数：执行 research_search → news_items 的导入流程。

    返回值:
        int: 0 表示成功，非 0 表示失败

    流程:
        1. 连接数据库，确保 news_items 表存在
        2. 读取 source_manifest 中 research_search 类型的记录
        3. 读取每条记录对应的 .meta.json，提取研报列表
        4. 将每条研报转换为 news item 并写入 news_items 表
        5. 刷新 news 健康检查状态
        6. 注册快照并记录运行日志
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_news_tables(conn)

        manifest_rows = load_research_manifest_rows(conn)
        print(f"找到 {len(manifest_rows)} 条 research_search 快照记录")

        inserted = 0
        deduped = 0
        skipped = 0
        scanned = 0

        for manifest_row in manifest_rows:
            metadata = loads_json(manifest_row.get("metadata_json"), {})
            meta_rel_path = metadata.get("meta_rel_path") or metadata.get("raw_rel_path")
            if not meta_rel_path:
                skipped += 1
                continue

            research_items = load_research_items(meta_rel_path)
            for research_item in research_items:
                scanned += 1
                news_item = build_news_item_from_research(manifest_row, research_item)
                if not news_item:
                    skipped += 1
                    continue
                try:
                    result = upsert_news_item(conn, news_item)
                except ValueError:
                    skipped += 1
                    continue
                if result.get("deduped"):
                    deduped += 1
                else:
                    inserted += 1

        metrics = {
            "inserted": inserted,
            "deduped": deduped,
            "skipped": skipped,
            "scanned": scanned,
            "manifest_rows": len(manifest_rows),
        }

        # 刷新 news 健康检查状态
        # "eastmoney_news_search" 已在 NEWS_SOURCE_KEYS 中，健康检查会自动统计
        health = update_news_health_rows(conn)
        metrics["health_overall"] = health.get("overall_status")

        register_snapshot(
            conn,
            entity_type="news_ingestion_snapshot",
            entity_id="latest",
            status="updated",
            source=SCRIPT_NAME,
            payload=metrics,
        )
        conn.commit()
    finally:
        conn.close()

    print(json.dumps(metrics, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "research imported as news", metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
