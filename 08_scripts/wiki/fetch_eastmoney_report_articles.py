#!/usr/bin/env python3
"""Fetch Eastmoney public report detail pages and PDF originals from existing report-search snapshots."""

import argparse
import json
import re
import sqlite3
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from html import unescape
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_external_sources import html_snapshot, persist_external_snapshot, truncate_text
from smr_paths import env_or_project_path, project_path
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import resolve_equity_targets
from smr_wiki import slugify

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
REPORT_INFO_URL = "https://data.eastmoney.com/report/info/{info_code}.html"
REPORT_PDF_URL = "https://pdf.dfcfw.com/pdf/H3_{info_code}_1.pdf"

ZWINFO_RE = re.compile(r"var\s+zwinfo=\s*(\{.*?\})\s*;", re.S)
TITLE_RE = re.compile(r'<h1 id="zw-title">(.*?)</h1>', re.S)
CONTENT_RE = re.compile(r'<div id="ctx-content" class="ctx-content">(.*?)</div>', re.S)
PDF_LINK_RE = re.compile(r'<a class="pdf-link" href="([^"]+)"')


def clean_tags(*values):
    return [value for value in values if value]


def normalize_text(text):
    return " ".join(unescape(str(text or "")).split())


def normalize_multiline_text(text):
    lines = []
    for raw_line in str(text or "").replace("\r", "\n").split("\n"):
        cleaned = normalize_text(raw_line.replace("\u3000", " "))
        if cleaned:
            lines.append(cleaned)
    return "\n\n".join(lines)


def normalize_published_at(text):
    cleaned = normalize_text(text).replace(".000", "")
    return cleaned


def canonicalize_url(url, strip_query=False):
    parsed = urllib.parse.urlparse(url or "")
    if not parsed.scheme:
        parsed = parsed._replace(scheme="https")
    elif parsed.scheme == "http":
        parsed = parsed._replace(scheme="https")
    if strip_query:
        parsed = parsed._replace(query="", fragment="")
    return urllib.parse.urlunparse(parsed)


def report_detail_url(info_code):
    return REPORT_INFO_URL.format(info_code=info_code)


def report_pdf_url(info_code, attach_url=""):
    return canonicalize_url(attach_url or REPORT_PDF_URL.format(info_code=info_code), strip_query=True)


def snapshot_source_id(provider, ts_code, info_code):
    stable_key = f"{ts_code}_{info_code}"
    return f"external_source__{slugify(provider)}__{slugify(stable_key)[:120]}"


def snapshot_exists_on_disk(ts_code, info_code, source_kind):
    entity_dir = project_path("11_smr_wiki", "raw", "external", "stock", slugify(ts_code))
    if not entity_dir.exists():
        return False
    pattern = f"*/{info_code}__{slugify(source_kind)}__*.meta.json"
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


def fetch_url(url, referer):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,*/*;q=0.8",
            "Referer": referer,
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        raw_bytes = response.read()
        content_type = response.headers.get("Content-Type", "")
        charset = response.headers.get_content_charset() or "utf-8"
        text = ""
        if "html" in content_type.lower() or "text" in content_type.lower():
            text = raw_bytes.decode(charset, errors="replace")
        return {
            "raw_bytes": raw_bytes,
            "text": text,
            "content_type": content_type,
            "final_url": response.geturl(),
            "status_code": response.getcode(),
        }


def resolve_targets(conn, args):
    return resolve_equity_targets(
        conn,
        explicit_ts_codes=args.ts_code,
        profile_name=args.profile,
        pool_types=args.pool_type,
        allowed_markets=["SZ", "SH", "BJ"],
        limit=args.limit,
    )


def latest_report_search_meta_path(conn, ts_code):
    row = conn.execute(
        """
        SELECT metadata_json
        FROM source_manifest
        WHERE source_type='external_source_snapshot'
          AND entity_id=?
          AND json_extract(metadata_json, '$.source_kind')='research_search'
        ORDER BY datetime(updated_at) DESC, datetime(created_at) DESC, source_id DESC
        LIMIT 1
        """,
        (ts_code,),
    ).fetchone()
    if row is None:
        return None
    metadata = json.loads(row[0] or "{}")
    meta_rel_path = metadata.get("meta_rel_path")
    if not meta_rel_path:
        return None
    return project_path(meta_rel_path)


def load_report_candidates(conn, ts_code, report_limit):
    meta_path = latest_report_search_meta_path(conn, ts_code)
    if meta_path is None or not meta_path.exists():
        return None, []
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["_meta_rel_path"] = str(meta_path.relative_to(project_path()))
    items = meta.get("items") or []
    candidates = []
    seen = set()
    for item in items:
        info_code = item.get("infoCode")
        if not info_code or info_code in seen:
            continue
        seen.add(info_code)
        candidates.append(item)
        if len(candidates) >= report_limit:
            break
    return meta, candidates


def build_summary(body_text):
    for raw_line in body_text.splitlines():
        line = normalize_text(raw_line)
        if len(line) < 16:
            continue
        if line in {"事件", "投资要点", "盈利预测", "风险提示"}:
            continue
        return truncate_text(line, limit=240)
    return ""


def extract_report_page(html_text, fallback_item):
    info = {}
    match = ZWINFO_RE.search(html_text)
    if match:
        try:
            info = json.loads(match.group(1))
        except json.JSONDecodeError:
            info = {}

    title_match = TITLE_RE.search(html_text)
    title = normalize_text(info.get("notice_title") or (title_match.group(1) if title_match else "") or fallback_item.get("title"))
    published_at = normalize_published_at(info.get("eitime") or info.get("notice_date") or fallback_item.get("publishDate"))
    org_name = normalize_text(info.get("source_sample_name") or fallback_item.get("orgSName") or fallback_item.get("orgName"))
    researcher = normalize_text(info.get("researcher") or fallback_item.get("researcher"))
    rating_name = normalize_text(fallback_item.get("emRatingName") or fallback_item.get("sRatingName"))
    attach_url = report_pdf_url(fallback_item.get("infoCode"), info.get("attach_url") or "")
    content = normalize_multiline_text(info.get("notice_content"))

    if not content:
        body_match = CONTENT_RE.search(html_text)
        body_html = body_match.group(1) if body_match else ""
        _unused_title, body_text = html_snapshot(body_html)
        content = normalize_multiline_text(body_text)

    if not info.get("attach_url"):
        pdf_match = PDF_LINK_RE.search(html_text)
        if pdf_match:
            attach_url = report_pdf_url(fallback_item.get("infoCode"), pdf_match.group(1))

    return {
        "title": title or normalize_text(fallback_item.get("title")),
        "published_at": published_at,
        "org_name": org_name,
        "researcher": researcher,
        "rating_name": rating_name,
        "body_text": truncate_text(content, limit=10000),
        "summary": build_summary(content),
        "attach_url": attach_url,
        "attach_pages": str(info.get("attach_pages") or fallback_item.get("attachPages") or ""),
        "attach_size": str(info.get("attach_size") or fallback_item.get("attachSize") or ""),
    }


def build_article_body_text(target, info_code, fields, detail_url):
    lines = [
        f"证券代码：{target['ts_code']}",
        f"证券简称：{target['name']}",
        f"研报编号：{info_code}",
        f"发布时间：{fields['published_at'] or '-'}",
        f"发布机构：{fields['org_name'] or '-'}",
        f"研究员：{fields['researcher'] or '-'}",
        f"投资评级：{fields['rating_name'] or '-'}",
        f"详情页链接：{detail_url}",
    ]
    if fields["attach_url"]:
        lines.append(f"PDF原文：{fields['attach_url']}")
    lines.append("")
    if fields["summary"]:
        lines.extend(["摘要：", fields["summary"], ""])
    lines.extend(["正文：", fields["body_text"] or "(empty)"])
    return truncate_text("\n".join(lines), limit=12000)


def build_pdf_body_text(target, info_code, fields, detail_url, pdf_url):
    lines = [
        f"证券代码：{target['ts_code']}",
        f"证券简称：{target['name']}",
        f"研报编号：{info_code}",
        f"发布时间：{fields['published_at'] or '-'}",
        f"发布机构：{fields['org_name'] or '-'}",
        f"研究员：{fields['researcher'] or '-'}",
        f"投资评级：{fields['rating_name'] or '-'}",
        f"详情页链接：{detail_url}",
        f"PDF原文：{pdf_url}",
    ]
    if fields["attach_pages"]:
        lines.append(f"PDF页数：{fields['attach_pages']}")
    if fields["attach_size"]:
        lines.append(f"PDF大小KB：{fields['attach_size']}")
    lines.append("")
    if fields["summary"]:
        lines.extend(["摘要：", fields["summary"]])
    return truncate_text("\n".join(lines), limit=4000)


def persist_article_snapshot(target, search_meta, item, page_result, fields, fetched_at):
    info_code = item["infoCode"]
    detail_url = canonicalize_url(page_result["final_url"], strip_query=True)
    published_at = fields["published_at"]
    bucket_date = (published_at[:10] if published_at else fetched_at[:10]) or fetched_at[:10]
    title = f"{target['ts_code']} 东方财富研报正文 {fields['title'] or info_code}"
    return persist_external_snapshot(
        title=title,
        fetched_at=fetched_at,
        entity_type="stock",
        entity_id=target["ts_code"],
        source_kind="research_article",
        source_url=detail_url,
        source_domain=urllib.parse.urlparse(detail_url).netloc,
        content_type=page_result["content_type"] or "text/html; charset=utf-8",
        raw_bytes=page_result["raw_bytes"],
        raw_extension=".html",
        note=f"eastmoney report article for {target['name']}",
        tags=clean_tags("eastmoney", "public_research", "report_detail"),
        body_text=build_article_body_text(target, info_code, fields, detail_url),
        metadata={
            "requested_url": report_detail_url(info_code),
            "search_snapshot_meta_rel_path": str(search_meta.get("_meta_rel_path") or ""),
            "status_code": page_result["status_code"],
            "info_code": info_code,
            "published_at": published_at,
            "org_name": fields["org_name"],
            "researcher": fields["researcher"],
            "rating_name": fields["rating_name"],
            "attach_url": fields["attach_url"],
            "attach_pages": fields["attach_pages"],
            "attach_size": fields["attach_size"],
            "summary": fields["summary"],
            "search_item": item,
        },
        extra_frontmatter={
            "provider": "eastmoney_report_article",
            "announcement_id": f"{target['ts_code']}_{info_code}",
            "published_at": published_at,
            "org_name": fields["org_name"],
            "researcher": fields["researcher"],
            "rating_name": fields["rating_name"],
            "info_code": info_code,
            "pdf_url": fields["attach_url"],
        },
        stable_key=info_code,
        bucket_date=bucket_date,
    )


def persist_pdf_snapshot(target, search_meta, item, pdf_result, fields, fetched_at):
    info_code = item["infoCode"]
    detail_url = report_detail_url(info_code)
    pdf_url = canonicalize_url(pdf_result["final_url"], strip_query=True)
    published_at = fields["published_at"]
    bucket_date = (published_at[:10] if published_at else fetched_at[:10]) or fetched_at[:10]
    title = f"{target['ts_code']} 东方财富研报PDF {fields['title'] or info_code}"
    return persist_external_snapshot(
        title=title,
        fetched_at=fetched_at,
        entity_type="stock",
        entity_id=target["ts_code"],
        source_kind="research_pdf",
        source_url=pdf_url,
        source_domain=urllib.parse.urlparse(pdf_url).netloc,
        content_type=pdf_result["content_type"] or "application/pdf",
        raw_bytes=pdf_result["raw_bytes"],
        raw_extension=".pdf",
        note=f"eastmoney report pdf for {target['name']}",
        tags=clean_tags("eastmoney", "public_research", "report_pdf"),
        body_text=build_pdf_body_text(target, info_code, fields, detail_url, pdf_url),
        metadata={
            "requested_url": fields["attach_url"] or report_pdf_url(info_code),
            "detail_url": detail_url,
            "search_snapshot_meta_rel_path": str(search_meta.get("_meta_rel_path") or ""),
            "status_code": pdf_result["status_code"],
            "info_code": info_code,
            "published_at": published_at,
            "org_name": fields["org_name"],
            "researcher": fields["researcher"],
            "rating_name": fields["rating_name"],
            "attach_pages": fields["attach_pages"],
            "attach_size": fields["attach_size"],
            "summary": fields["summary"],
            "search_item": item,
        },
        extra_frontmatter={
            "provider": "eastmoney_report_pdf",
            "announcement_id": f"{target['ts_code']}_{info_code}",
            "published_at": published_at,
            "org_name": fields["org_name"],
            "researcher": fields["researcher"],
            "rating_name": fields["rating_name"],
            "info_code": info_code,
            "detail_url": detail_url,
        },
        stable_key=info_code,
        bucket_date=bucket_date,
    )


def main():
    parser = argparse.ArgumentParser(description="Fetch Eastmoney report detail pages from existing report-search snapshots")
    parser.add_argument("--ts-code", action="append", help="Specific A-share ts_code; can be repeated")
    parser.add_argument("--profile", default="standard_external", help="Coverage profile from research_amplification_registry.md")
    parser.add_argument("--pool-type", action="append", help="Override pool type; can be repeated")
    parser.add_argument("--limit", type=int, help="Override maximum number of target symbols")
    parser.add_argument("--report-limit", type=int, default=2, help="Maximum report detail pages to persist for each symbol")
    parser.add_argument("--skip-pdf", action="store_true", help="Skip downloading PDF originals")
    parser.add_argument("--force", action="store_true", help="Fetch even if the report detail already exists")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    targets = resolve_targets(conn, args)
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    article_persisted = []
    article_skipped = []
    pdf_persisted = []
    pdf_skipped = []
    empty = []
    failed = []
    detail_cache = {}

    for target in targets:
        search_meta, items = load_report_candidates(conn, target["ts_code"], args.report_limit)
        if search_meta is None:
            empty.append({"ts_code": target["ts_code"], "reason": "missing_report_search_snapshot"})
            continue
        if not items:
            empty.append({"ts_code": target["ts_code"], "reason": "report_search_snapshot_has_no_items"})
            continue

        for item in items:
            info_code = item.get("infoCode") or ""
            if not info_code:
                failed.append({"ts_code": target["ts_code"], "error": "missing_info_code"})
                continue

            detail_url = report_detail_url(info_code)
            article_already_exists = snapshot_exists(
                conn,
                target["ts_code"],
                info_code,
                provider="eastmoney_report_article",
                source_kind="research_article",
            )

            fields = None
            page_result = None
            if (not args.force) and article_already_exists:
                article_skipped.append({"ts_code": target["ts_code"], "info_code": info_code, "reason": "already_exists"})
            else:
                try:
                    if detail_url not in detail_cache:
                        detail_cache[detail_url] = fetch_url(detail_url, referer="https://data.eastmoney.com/report/stock.jshtml")
                    page_result = detail_cache[detail_url]
                    final_url = canonicalize_url(page_result["final_url"], strip_query=True)
                    if "eastmoney.com" not in urllib.parse.urlparse(final_url).netloc:
                        article_skipped.append({"ts_code": target["ts_code"], "info_code": info_code, "reason": "unsupported_domain"})
                    else:
                        fields = extract_report_page(page_result["text"], item)
                        snapshot = persist_article_snapshot(target, search_meta, item, page_result, fields, fetched_at)
                        article_persisted.append(
                            {
                                "ts_code": target["ts_code"],
                                "info_code": info_code,
                                "title": snapshot["title"],
                                "markdown_rel_path": snapshot["markdown_rel_path"],
                                "raw_rel_path": snapshot["raw_rel_path"],
                            }
                        )
                except Exception as exc:
                    failed.append({"ts_code": target["ts_code"], "info_code": info_code, "stage": "article", "error": str(exc)})
                    continue

            if args.skip_pdf:
                continue

            if fields is None:
                if page_result is None:
                    try:
                        if detail_url not in detail_cache:
                            detail_cache[detail_url] = fetch_url(detail_url, referer="https://data.eastmoney.com/report/stock.jshtml")
                        page_result = detail_cache[detail_url]
                        fields = extract_report_page(page_result["text"], item)
                    except Exception as exc:
                        failed.append({"ts_code": target["ts_code"], "info_code": info_code, "stage": "pdf_prep", "error": str(exc)})
                        continue
                else:
                    fields = extract_report_page(page_result["text"], item)

            pdf_url = fields["attach_url"] or report_pdf_url(info_code)
            pdf_already_exists = snapshot_exists(
                conn,
                target["ts_code"],
                info_code,
                provider="eastmoney_report_pdf",
                source_kind="research_pdf",
            )
            if (not args.force) and pdf_already_exists:
                pdf_skipped.append({"ts_code": target["ts_code"], "info_code": info_code, "reason": "already_exists"})
                continue

            try:
                pdf_result = fetch_url(pdf_url, referer=detail_url)
                final_pdf_url = canonicalize_url(pdf_result["final_url"], strip_query=True)
                if "dfcfw.com" not in urllib.parse.urlparse(final_pdf_url).netloc:
                    pdf_skipped.append({"ts_code": target["ts_code"], "info_code": info_code, "reason": "unsupported_pdf_domain"})
                    continue
                snapshot = persist_pdf_snapshot(target, search_meta, item, pdf_result, fields, fetched_at)
                pdf_persisted.append(
                    {
                        "ts_code": target["ts_code"],
                        "info_code": info_code,
                        "title": snapshot["title"],
                        "markdown_rel_path": snapshot["markdown_rel_path"],
                        "raw_rel_path": snapshot["raw_rel_path"],
                    }
                )
            except Exception as exc:
                failed.append({"ts_code": target["ts_code"], "info_code": info_code, "stage": "pdf", "error": str(exc)})

    register_snapshot(
        conn,
        entity_type="eastmoney_report_article_batch",
        entity_id=datetime.now().strftime("%Y-%m-%d"),
        status="fetched" if (article_persisted or pdf_persisted) else "empty",
        source="fetch_eastmoney_report_articles.py",
        relationships={
            "target_count": len(targets),
            "profile": args.profile,
            "requested_pool_types": args.pool_type or [],
            "limit": args.limit,
            "report_limit": args.report_limit,
            "skip_pdf": args.skip_pdf,
            "force": args.force,
        },
        payload={
            "article_persisted_count": len(article_persisted),
            "article_skipped_count": len(article_skipped),
            "pdf_persisted_count": len(pdf_persisted),
            "pdf_skipped_count": len(pdf_skipped),
            "empty_count": len(empty),
            "failed_count": len(failed),
            "article_persisted": article_persisted[:20],
            "article_skipped": article_skipped[:20],
            "pdf_persisted": pdf_persisted[:20],
            "pdf_skipped": pdf_skipped[:20],
            "empty": empty[:20],
            "failed": failed[:20],
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "fetch_eastmoney_report_articles.py",
        "success" if not failed else "warning",
        "eastmoney report detail pages fetched",
        {
            "target_count": len(targets),
            "profile": args.profile,
            "requested_pool_types": args.pool_type or [],
            "limit": args.limit,
            "report_limit": args.report_limit,
            "article_persisted_count": len(article_persisted),
            "article_skipped_count": len(article_skipped),
            "pdf_persisted_count": len(pdf_persisted),
            "pdf_skipped_count": len(pdf_skipped),
            "empty_count": len(empty),
            "failed_count": len(failed),
            "article_persisted": article_persisted[:20],
            "article_skipped": article_skipped[:20],
            "pdf_persisted": pdf_persisted[:20],
            "pdf_skipped": pdf_skipped[:20],
            "empty": empty[:20],
            "failed": failed[:20],
        },
    )

    print(f"Eastmoney report articles: {len(article_persisted)}")
    for item in article_persisted[:20]:
        print(f"- article | {item['ts_code']} | {item['info_code']} -> {item['markdown_rel_path']}")
    print(f"Eastmoney report pdfs: {len(pdf_persisted)}")
    for item in pdf_persisted[:20]:
        print(f"- pdf | {item['ts_code']} | {item['info_code']} -> {item['markdown_rel_path']}")
    if article_skipped:
        print("Article skipped:")
        for item in article_skipped[:20]:
            print(f"- {item['ts_code']} | {item['info_code']}: {item['reason']}")
    if pdf_skipped:
        print("PDF skipped:")
        for item in pdf_skipped[:20]:
            print(f"- {item['ts_code']} | {item['info_code']}: {item['reason']}")
    if empty:
        print("Empty:")
        for item in empty[:20]:
            print(f"- {item['ts_code']}: {item['reason']}")
    if failed:
        print("Failures:")
        for item in failed[:20]:
            print(f"- {item['ts_code']} | {item.get('info_code', '-')}: {item['stage']} | {item['error']}")


if __name__ == "__main__":
    main()
