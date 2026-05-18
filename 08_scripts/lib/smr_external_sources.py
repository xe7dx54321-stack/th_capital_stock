#!/usr/bin/env python3
"""Helpers for persisting external raw source snapshots."""

import hashlib
import json
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

from smr_paths import project_path, relative_to_project
from smr_wiki import slugify

EXTERNAL_RAW_DIR = project_path("11_smr_wiki", "raw", "external")


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.in_title = False
        self.title_parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False
        if tag.lower() in {"p", "div", "section", "article", "h1", "h2", "h3", "li", "br"}:
            self.parts.append("\n")

    def handle_data(self, data):
        text = unescape(data or "")
        if not text.strip():
            return
        if self.in_title:
            self.title_parts.append(text.strip())
        self.parts.append(text.strip())

    def title(self):
        return " ".join(self.title_parts).strip()

    def text(self):
        cleaned = "\n".join(line.strip() for line in " ".join(self.parts).splitlines())
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
        return cleaned.strip()


def html_snapshot(text):
    parser = TextExtractor()
    parser.feed(text)
    return parser.title(), parser.text()


def truncate_text(text, limit=12000):
    cleaned = (text or "").strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def target_paths(entity_type, entity_id, source_kind, title, fetched_at, raw_extension, stable_key=None, bucket_date=None):
    entity_dir = EXTERNAL_RAW_DIR / slugify(entity_type) / slugify(entity_id) / (bucket_date or fetched_at[:10])
    stamp = fetched_at.replace("-", "").replace(":", "").replace(" ", "_")
    stem_prefix = slugify(stable_key) if stable_key else stamp
    digest = hashlib.sha1(f"{stable_key or stamp}|{source_kind}|{title}".encode("utf-8")).hexdigest()[:10]
    stem = "__".join(
        [
            stem_prefix[:40],
            slugify(source_kind)[:24],
            f"{slugify(title)[:32]}_{digest}",
        ]
    )
    raw_extension = raw_extension if raw_extension.startswith(".") else f".{raw_extension}"
    return {
        "dir": entity_dir,
        "markdown": entity_dir / f"{stem}.md",
        "raw": entity_dir / f"{stem}.raw{raw_extension}",
        "meta": entity_dir / f"{stem}.meta.json",
    }


def markdown_snapshot(
    title,
    fetched_at,
    entity_type,
    entity_id,
    source_kind,
    source_url,
    source_domain,
    content_type,
    raw_rel_path,
    meta_rel_path,
    note,
    tags,
    body_text,
    extra_frontmatter=None,
):
    tag_text = ", ".join(tags)
    lines = [
        "---",
        f"title: {title}",
        f"source_url: {source_url}",
        f"source_kind: {source_kind}",
        f"entity_type: {entity_type}",
        f"entity_id: {entity_id}",
        f"source_domain: {source_domain}",
        f"content_type: {content_type}",
        f"fetched_at: {fetched_at}",
        f"raw_rel_path: {raw_rel_path}",
        f"meta_rel_path: {meta_rel_path}",
        f"tags: {tag_text}",
    ]
    for key, value in (extra_frontmatter or {}).items():
        if value in (None, ""):
            continue
        lines.append(f"{key}: {value}")
    lines.extend(
        [
            "---",
            "",
            f"# {title}",
            "",
            "## Snapshot Meta",
            "",
            f"- fetched_at: {fetched_at}",
            f"- source_kind: {source_kind}",
            f"- source_url: {source_url}",
            f"- source_domain: {source_domain}",
            f"- content_type: {content_type}",
        ]
    )
    if note:
        lines.append(f"- note: {note}")
    lines.extend(
        [
            "",
            "## Extracted Text",
            "",
            body_text or "(empty)",
            "",
        ]
    )
    return "\n".join(lines)


def persist_external_snapshot(
    *,
    title,
    fetched_at,
    entity_type,
    entity_id,
    source_kind,
    source_url,
    source_domain,
    content_type,
    raw_bytes,
    raw_extension,
    note=None,
    tags=None,
    body_text="",
    metadata=None,
    extra_frontmatter=None,
    stable_key=None,
    bucket_date=None,
):
    EXTERNAL_RAW_DIR.mkdir(parents=True, exist_ok=True)
    paths = target_paths(
        entity_type,
        entity_id,
        source_kind,
        title,
        fetched_at,
        raw_extension,
        stable_key=stable_key,
        bucket_date=bucket_date,
    )
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["raw"].write_bytes(raw_bytes)

    metadata_payload = {
        "title": title,
        "source_url": source_url,
        "source_kind": source_kind,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "source_domain": source_domain,
        "content_type": content_type,
        "fetched_at": fetched_at,
        "note": note,
        "tags": tags or [],
        "raw_rel_path": relative_to_project(paths["raw"]),
    }
    metadata_payload.update(metadata or {})
    paths["meta"].write_text(json.dumps(metadata_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown = markdown_snapshot(
        title=title,
        fetched_at=fetched_at,
        entity_type=entity_type,
        entity_id=entity_id,
        source_kind=source_kind,
        source_url=source_url,
        source_domain=source_domain,
        content_type=content_type,
        raw_rel_path=relative_to_project(paths["raw"]),
        meta_rel_path=relative_to_project(paths["meta"]),
        note=note,
        tags=tags or [],
        body_text=body_text,
        extra_frontmatter=extra_frontmatter,
    )
    paths["markdown"].write_text(markdown, encoding="utf-8")
    return {
        "title": title,
        "markdown_rel_path": relative_to_project(paths["markdown"]),
        "raw_rel_path": relative_to_project(paths["raw"]),
        "meta_rel_path": relative_to_project(paths["meta"]),
    }
