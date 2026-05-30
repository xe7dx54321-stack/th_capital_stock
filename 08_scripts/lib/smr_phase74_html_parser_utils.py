#!/usr/bin/env python3
"""Phase 74: HTML parser common utilities."""
import re, hashlib
from urllib.parse import urljoin
from typing import Any

def remove_scripts_styles(html: str) -> str:
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    return html

def extract_visible_text(html: str) -> str:
    html = remove_scripts_styles(html)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"&nbsp;", " ", html)
    html = re.sub(r"&amp;", "&", html)
    html = re.sub(r"&lt;", "<", html)
    html = re.sub(r"&gt;", ">", html)
    html = re.sub(r"&quot;", chr(34), html)
    html = re.sub(r"&#?\w+;", " ", html)
    html = re.sub(r"\s+", " ", html).strip()
    return html

def extract_links(html: str, base_url: str = "") -> list:
    links = []
    pattern = re.compile(r'<a[^>]+href=["\x27]([^"\x27\s>]+)["\x27][^>]*>(.*?)</a>', re.DOTALL | re.IGNORECASE)
    for m in pattern.finditer(html):
        url = m.group(1)
        anchor = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if base_url:
            url = urljoin(base_url, url)
        links.append({"url": url, "anchor_text": anchor[:200]})
    return links

def detect_pdf_links(links: list) -> list:
    return [l for l in links if l["url"].lower().endswith(".pdf") or ".pdf?" in l["url"].lower()]

def extract_dates(text: str) -> list:
    dates = re.findall(r"\d{4}[-/.]\d{2}[-/.]\d{2}", text)
    return list(set(dates))[:50]

def remove_boilerplate(text: str) -> str:
    lines = text.split("\n")
    filtered = []
    for line in lines:
        s = line.strip()
        if len(s) < 5 and not any(c.isalpha() for c in s):
            continue
        bp_markers = ["copyright", "all rights reserved", "技术支持", "备案号", "京ICP", "沪ICP"]
        if any(m in s.lower() for m in bp_markers):
            continue
        filtered.append(s)
    return "\n".join(filtered)

def text_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]

def chinese_ratio(text: str) -> float:
    if not text:
        return 0.0
    ch = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    return ch / max(len(text), 1)

def is_metadata_only(text: str) -> bool:
    if len(text) < 100:
        return True
    meta = ["证券代码", "证券简称", "公告日期", "公告编号", "announcement date", "stock code"]
    ratio = sum(1 for m in meta if m.lower() in text.lower()) / max(len(meta), 1)
    return ratio >= 0.5 and len(text) < 500
