#!/usr/bin/env python3
"""Extract text from Eastmoney report PDF snapshots and persist derived text snapshots."""

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

try:
    from pdfminer.high_level import extract_text as pdf_extract_text
except Exception as exc:  # pragma: no cover - environment-specific guard
    raise SystemExit(
        "pdfminer.six is required. Install with: python3 -m pip install --user -i https://pypi.tuna.tsinghua.edu.cn/simple pdfminer.six"
    ) from exc


DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")


def normalize_text(text):
    return " ".join(str(text or "").split())


def normalize_multiline_text(text):
    cleaned = str(text or "").replace("\r", "\n").replace("\x0c", "\n")
    lines = []
    for raw_line in cleaned.split("\n"):
        line = re.sub(r"\s+", " ", raw_line).strip()
        if line:
            lines.append(line)

    merged = []
    for line in lines:
        if re.fullmatch(r"\[Table_[^\]]+\]", line):
            continue
        if merged and re.fullmatch(r"[0-9]{1,3}", line):
            continue
        if merged and re.fullmatch(r"[\u4e00-\u9fffA-Za-z]{1,2}", line):
            merged[-1] = f"{merged[-1]}{line}"
            continue
        merged.append(line)
    return "\n\n".join(merged)


def snapshot_source_id(provider, ts_code, info_code):
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
        (ts_code, snapshot_source_id(provider, ts_code, info_code)),
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


def load_pdf_candidates(conn, ts_code, pdf_limit):
    rows = conn.execute(
        """
        SELECT metadata_json
        FROM source_manifest
        WHERE source_type='external_source_snapshot'
          AND entity_id=?
          AND json_extract(metadata_json, '$.source_kind')='research_pdf'
        ORDER BY datetime(updated_at) DESC, datetime(created_at) DESC, source_id DESC
        LIMIT ?
        """,
        (ts_code, pdf_limit),
    ).fetchall()
    candidates = []
    seen = set()
    for (metadata_json,) in rows:
        manifest_meta = json.loads(metadata_json or "{}")
        meta_rel_path = manifest_meta.get("meta_rel_path")
        raw_rel_path = manifest_meta.get("raw_rel_path")
        if not meta_rel_path or not raw_rel_path:
            continue
        meta_path = project_path(meta_rel_path)
        raw_path = project_path(raw_rel_path)
        if (not meta_path.exists()) or (not raw_path.exists()):
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        info_code = meta.get("info_code")
        if not info_code or info_code in seen:
            continue
        seen.add(info_code)
        meta["_meta_rel_path"] = meta_rel_path
        meta["_raw_rel_path"] = raw_rel_path
        candidates.append(meta)
    return candidates


def build_summary(text, fallback=""):
    for raw_line in str(text or "").splitlines():
        line = normalize_text(raw_line)
        if len(line) >= 20:
            return truncate_text(line, limit=240)
    return truncate_text(normalize_text(fallback), limit=240)


def build_body_text(target, meta, extracted_text):
    lines = [
        f"证券代码：{target['ts_code']}",
        f"证券简称：{target['name']}",
        f"研报编号：{meta.get('info_code') or '-'}",
        f"发布时间：{meta.get('published_at') or '-'}",
        f"发布机构：{meta.get('org_name') or '-'}",
        f"研究员：{meta.get('researcher') or '-'}",
        f"投资评级：{meta.get('rating_name') or '-'}",
        f"详情页链接：{meta.get('detail_url') or '-'}",
        f"PDF原文：{meta.get('source_url') or '-'}",
    ]
    if meta.get("attach_pages"):
        lines.append(f"PDF页数：{meta.get('attach_pages')}")
    if meta.get("attach_size"):
        lines.append(f"PDF大小KB：{meta.get('attach_size')}")
    lines.append("")
    summary = meta.get("summary") or build_summary(extracted_text)
    if summary:
        lines.extend(["摘要：", summary, ""])
    lines.extend(["全文抽取：", truncate_text(extracted_text, limit=12000)])
    return "\n".join(lines)


def persist_text_snapshot(target, meta, extracted_text, fetched_at):
    info_code = meta["info_code"]
    published_at = normalize_text(meta.get("published_at"))
    bucket_date = (published_at[:10] if published_at else fetched_at[:10]) or fetched_at[:10]
    title = f"{target['ts_code']} 东方财富研报PDF文本 {meta.get('search_item', {}).get('title') or info_code}"
    raw_text = (extracted_text.strip() + "\n").encode("utf-8")
    return persist_external_snapshot(
        title=title,
        fetched_at=fetched_at,
        entity_type="stock",
        entity_id=target["ts_code"],
        source_kind="research_pdf_text",
        source_url=meta.get("source_url") or "",
        source_domain=meta.get("source_domain") or "pdf.dfcfw.com",
        content_type="text/plain; charset=utf-8",
        raw_bytes=raw_text,
        raw_extension=".txt",
        note=f"pdf text extracted from eastmoney report for {target['name']}",
        tags=["eastmoney", "public_research", "report_pdf_text"],
        body_text=build_body_text(target, meta, extracted_text),
        metadata={
            "info_code": info_code,
            "published_at": published_at,
            "org_name": meta.get("org_name"),
            "researcher": meta.get("researcher"),
            "rating_name": meta.get("rating_name"),
            "attach_pages": meta.get("attach_pages"),
            "attach_size": meta.get("attach_size"),
            "detail_url": meta.get("detail_url"),
            "pdf_meta_rel_path": meta.get("_meta_rel_path"),
            "pdf_raw_rel_path": meta.get("_raw_rel_path"),
            "extract_method": "pdfminer.six",
            "summary": meta.get("summary") or build_summary(extracted_text),
            "search_item": meta.get("search_item"),
        },
        extra_frontmatter={
            "provider": "eastmoney_report_pdf_text",
            "announcement_id": f"{target['ts_code']}_{info_code}",
            "published_at": published_at,
            "org_name": meta.get("org_name"),
            "researcher": meta.get("researcher"),
            "rating_name": meta.get("rating_name"),
            "info_code": info_code,
            "detail_url": meta.get("detail_url"),
            "extract_method": "pdfminer.six",
        },
        stable_key=info_code,
        bucket_date=bucket_date,
    )


def main():
    parser = argparse.ArgumentParser(description="Extract text from Eastmoney report PDF snapshots")
    parser.add_argument("--ts-code", action="append", help="Specific A-share ts_code; can be repeated")
    parser.add_argument("--profile", default="standard_external", help="Coverage profile from research_amplification_registry.md")
    parser.add_argument("--pool-type", action="append", help="Override pool type; can be repeated")
    parser.add_argument("--limit", type=int, help="Override maximum number of target symbols")
    parser.add_argument("--pdf-limit", type=int, default=2, help="Maximum PDF snapshots to extract for each symbol")
    parser.add_argument("--force", action="store_true", help="Extract even if derived text snapshot already exists")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    targets = resolve_targets(conn, args)
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    persisted = []
    skipped = []
    empty = []
    failed = []

    for target in targets:
        candidates = load_pdf_candidates(conn, target["ts_code"], args.pdf_limit)
        if not candidates:
            empty.append({"ts_code": target["ts_code"], "reason": "missing_research_pdf_snapshot"})
            continue

        for meta in candidates:
            info_code = meta.get("info_code") or ""
            if not info_code:
                failed.append({"ts_code": target["ts_code"], "error": "missing_info_code"})
                continue
            if (not args.force) and snapshot_exists(
                conn,
                target["ts_code"],
                info_code,
                provider="eastmoney_report_pdf_text",
                source_kind="research_pdf_text",
            ):
                skipped.append({"ts_code": target["ts_code"], "info_code": info_code, "reason": "already_exists"})
                continue
            try:
                raw_path = project_path(meta["_raw_rel_path"])
                extracted_text = normalize_multiline_text(pdf_extract_text(str(raw_path)))
                if not extracted_text:
                    failed.append({"ts_code": target["ts_code"], "info_code": info_code, "error": "empty_extracted_text"})
                    continue
                snapshot = persist_text_snapshot(target, meta, extracted_text, fetched_at)
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
        entity_type="eastmoney_report_pdf_text_batch",
        entity_id=datetime.now().strftime("%Y-%m-%d"),
        status="fetched" if persisted else "empty",
        source="extract_eastmoney_report_pdf_text.py",
        relationships={
            "target_count": len(targets),
            "profile": args.profile,
            "requested_pool_types": args.pool_type or [],
            "limit": args.limit,
            "pdf_limit": args.pdf_limit,
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
        "extract_eastmoney_report_pdf_text.py",
        "success" if not failed else "warning",
        "eastmoney report pdf text extracted",
        {
            "target_count": len(targets),
            "profile": args.profile,
            "requested_pool_types": args.pool_type or [],
            "limit": args.limit,
            "pdf_limit": args.pdf_limit,
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

    print(f"Eastmoney report pdf text snapshots: {len(persisted)}")
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
