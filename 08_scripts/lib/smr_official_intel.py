#!/usr/bin/env python3
"""Helpers for official primary-source discovery across SEC and company IR sites."""

import html
import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path

from smr_external_sources import html_snapshot, truncate_text
from smr_paths import project_path
from smr_universe import ordered_unique, parse_markdown_table
from smr_wiki import slugify

OFFICIAL_INTEL_TARGET_REGISTRY_PATH = project_path("00_control", "official_intel_target_registry.md")

DEFAULT_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
DEFAULT_SEC_USER_AGENT = "SMR Research Bot/1.0 (research@localhost)"

DEFAULT_DISCOVERY_KEYWORDS = [
    "earnings",
    "results",
    "financial",
    "quarter",
    "annual",
    "report",
    "interim",
    "presentation",
    "slides",
    "transcript",
    "remarks",
    "webcast",
    "conference-call",
    "press-release",
    "sec",
    "filings",
    "10-k",
    "10-q",
    "20-f",
    "6-k",
    "8-k",
]
DEFAULT_EXCLUDE_KEYWORDS = [
    "facebook",
    "linkedin",
    "twitter",
    "instagram",
    "youtube",
    "weibo",
    "privacy",
    "terms",
    "career",
    "contact",
    "about",
    "mailto:",
    "javascript:",
    "favicon",
    ".css",
    ".js",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
]
PDF_HOST_ALLOWLIST = ("q4cdn.com", "alibabagroup.com", "microsoft.com", "sec.gov")


try:
    from pdfminer.high_level import extract_text as pdf_extract_text
except Exception:  # pragma: no cover - environment-specific import
    pdf_extract_text = None


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


def parse_int(value, default=None):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        return default


def normalize_csv_list(value):
    if value in (None, ""):
        return []
    if isinstance(value, str):
        raw_items = value.split(",")
    else:
        raw_items = value
    return ordered_unique(raw_items)


def normalize_space(text):
    return " ".join(str(text or "").split())


def normalize_multiline_text(text):
    cleaned = str(text or "").replace("\r", "\n").replace("\x0c", "\n")
    lines = []
    for raw_line in cleaned.split("\n"):
        line = re.sub(r"\s+", " ", raw_line).strip()
        if line:
            lines.append(line)
    return "\n\n".join(lines)


def parse_official_intel_target_registry(path_value=OFFICIAL_INTEL_TARGET_REGISTRY_PATH):
    sections = section_lines(path_value)
    rows = []
    for row in parse_markdown_table(sections.get("Targets", [])):
        target_key = str(row.get("Target Key") or "").strip()
        if not target_key:
            continue
        include_keywords = normalize_csv_list(row.get("Include Keywords")) or list(DEFAULT_DISCOVERY_KEYWORDS)
        exclude_keywords = normalize_csv_list(row.get("Exclude Keywords")) or list(DEFAULT_EXCLUDE_KEYWORDS)
        rows.append(
            {
                "target_key": target_key,
                "entity_type": str(row.get("Entity Type") or "").strip() or "stock",
                "entity_id": str(row.get("Entity ID") or "").strip(),
                "company_name": str(row.get("Company") or "").strip(),
                "market": str(row.get("Market") or "").strip().upper(),
                "sec_symbol": str(row.get("SEC Symbol") or "").strip().upper(),
                "ir_url": str(row.get("IR URL") or "").strip(),
                "include_keywords": [item.lower() for item in include_keywords],
                "exclude_keywords": [item.lower() for item in exclude_keywords],
                "max_links": parse_int(row.get("Max Links"), default=6) or 6,
                "status": str(row.get("Status") or "").strip() or "planned",
                "enabled": parse_bool(row.get("Enabled")),
                "notes": str(row.get("Notes") or "").strip(),
            }
        )
    return rows


def select_target_rows(target_rows, target_keys=None, entity_ids=None, enabled_only=True):
    key_filter = {item.strip() for item in (target_keys or []) if str(item).strip()}
    entity_filter = {item.strip() for item in (entity_ids or []) if str(item).strip()}
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


def build_request(url, user_agent=None, accept=None, extra_headers=None):
    headers = {
        "User-Agent": user_agent or DEFAULT_BROWSER_USER_AGENT,
        "Accept": accept or "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    headers.update(extra_headers or {})
    return urllib.request.Request(url, headers=headers)


def decode_body(raw_bytes, content_type):
    charset = None
    match = re.search(r"charset=([A-Za-z0-9._-]+)", str(content_type or ""), flags=re.I)
    if match:
        charset = match.group(1)
    candidates = [charset, "utf-8", "utf-8-sig", "latin-1"]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return raw_bytes.decode(candidate)
        except UnicodeDecodeError:
            continue
    return raw_bytes.decode("utf-8", errors="replace")


def fetch_url(url, timeout=30, user_agent=None, accept=None, extra_headers=None):
    request = build_request(sanitize_url(url), user_agent=user_agent, accept=accept, extra_headers=extra_headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw_bytes = response.read()
        content_type = response.headers.get("Content-Type", "")
        return {
            "bytes": raw_bytes,
            "text": decode_body(raw_bytes, content_type),
            "content_type": content_type,
            "final_url": response.geturl(),
            "status_code": response.getcode(),
            "headers": dict(response.headers.items()),
        }


def absolute_url(base_url, raw_url):
    return sanitize_url(urllib.parse.urljoin(base_url, str(raw_url or "").strip()))


def sanitize_url(raw_url):
    text = str(raw_url or "").strip()
    if not text:
        return text
    split = urllib.parse.urlsplit(text)
    path = urllib.parse.quote(split.path, safe="/:@+%~!$&'()*;,=")
    query = urllib.parse.quote(split.query, safe="=&?/:@+%~!$'()*;,[]")
    fragment = urllib.parse.quote(split.fragment, safe="=&?/:@+%~!$'()*;,[]")
    return urllib.parse.urlunsplit((split.scheme, split.netloc, path, query, fragment))


def host_key(url):
    return urllib.parse.urlparse(url).netloc.lower()


def same_root_host(left, right):
    left_host = host_key(left)
    right_host = host_key(right)
    if not left_host or not right_host:
        return False
    if left_host == right_host:
        return True
    left_parts = left_host.split(".")
    right_parts = right_host.split(".")
    return len(left_parts) >= 2 and len(right_parts) >= 2 and left_parts[-2:] == right_parts[-2:]


class LinkExtractor(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.links = []
        self.meta = {}
        self._title_parts = []
        self._in_title = False
        self._active_href = None
        self._active_text_parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        lower_tag = tag.lower()
        if lower_tag == "title":
            self._in_title = True
        if lower_tag == "meta":
            key = attrs.get("property") or attrs.get("name")
            content = attrs.get("content")
            if key and content:
                self.meta[key.lower()] = content
        if lower_tag == "a":
            href = attrs.get("href")
            if href:
                self._active_href = href
                self._active_text_parts = []

    def handle_endtag(self, tag):
        lower_tag = tag.lower()
        if lower_tag == "title":
            self._in_title = False
        if lower_tag == "a" and self._active_href:
            text = normalize_space(" ".join(self._active_text_parts))
            self.links.append(
                {
                    "href": self._active_href,
                    "url": absolute_url(self.base_url, self._active_href),
                    "text": text,
                }
            )
            self._active_href = None
            self._active_text_parts = []

    def handle_data(self, data):
        text = normalize_space(data)
        if not text:
            return
        if self._in_title:
            self._title_parts.append(text)
        if self._active_href:
            self._active_text_parts.append(text)

    @property
    def title(self):
        return normalize_space(" ".join(self._title_parts))


def extract_raw_urls(text):
    urls = []
    normalized_text = html.unescape(html.unescape(str(text or "")))
    for match in re.findall(r"https?://[^\s\"'<>]+", normalized_text, flags=re.I):
        url = sanitize_url(match.rstrip("),.;"))
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            continue
        urls.append(url)
    return ordered_unique(urls)


def guess_published_date(text, meta_map=None, url=None):
    meta_map = meta_map or {}
    candidates = [
        meta_map.get("article:published_time"),
        meta_map.get("publishdate"),
        meta_map.get("date"),
        meta_map.get("dc.date"),
        meta_map.get("og:updated_time"),
    ]
    if url:
        candidates.append(url)
    preview = str(text or "")[:3000]
    candidates.append(preview)

    month_pattern = (
        r"(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{1,2},\s+\d{4}"
    )
    for candidate in candidates:
        value = str(candidate or "").strip()
        if not value:
            continue
        iso_text = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(iso_text).strftime("%Y-%m-%d")
        except ValueError:
            pass
        try:
            return parsedate_to_datetime(value).strftime("%Y-%m-%d")
        except (TypeError, ValueError, IndexError, OverflowError):
            pass
        month_match = re.search(month_pattern, value, flags=re.I)
        if month_match:
            month_text = month_match.group(0)
            for pattern in ("%B %d, %Y", "%b %d, %Y"):
                try:
                    return datetime.strptime(month_text, pattern).strftime("%Y-%m-%d")
                except ValueError:
                    continue
        iso_match = re.search(r"(20\d{2}-\d{2}-\d{2})", value)
        if iso_match:
            return iso_match.group(1)
    return None


def response_extension(response):
    final_url = response.get("final_url") or ""
    suffix = Path(urllib.parse.urlparse(final_url).path).suffix.lower()
    if suffix:
        return suffix
    content_type = str(response.get("content_type") or "").lower()
    if "json" in content_type:
        return ".json"
    if "pdf" in content_type:
        return ".pdf"
    if "xml" in content_type:
        return ".xml"
    if "html" in content_type:
        return ".html"
    if "plain" in content_type or "text" in content_type:
        return ".txt"
    return ".bin"


def response_domain(response):
    return host_key(response.get("final_url") or "")


def extract_text_payload(response, title_hint=None):
    content_type = str(response.get("content_type") or "").lower()
    final_url = response.get("final_url") or ""
    raw_bytes = response.get("bytes") or b""
    text = response.get("text") or ""

    if "pdf" in content_type or final_url.lower().endswith(".pdf"):
        title = title_hint or Path(urllib.parse.urlparse(final_url).path).name or "official_pdf"
        extracted_text = ""
        if pdf_extract_text is not None:
            try:
                extracted_text = pdf_extract_text(io.BytesIO(raw_bytes))
            except Exception:
                extracted_text = ""
        normalized = normalize_multiline_text(extracted_text)
        return {
            "title": title,
            "body_text": truncate_text(normalized or "(pdf captured; text extraction unavailable)"),
            "text_kind": "pdf",
            "published_at": guess_published_date(normalized, url=final_url),
        }

    if "html" in content_type or "<html" in text.lower():
        extractor = LinkExtractor(final_url)
        extractor.feed(text)
        html_title, body_text = html_snapshot(text)
        return {
            "title": title_hint or extractor.title or html_title or Path(urllib.parse.urlparse(final_url).path).name or final_url,
            "body_text": truncate_text(body_text),
            "text_kind": "html",
            "published_at": guess_published_date(body_text, meta_map=extractor.meta, url=final_url),
        }

    normalized = normalize_multiline_text(text)
    return {
        "title": title_hint or Path(urllib.parse.urlparse(final_url).path).name or final_url,
        "body_text": truncate_text(normalized),
        "text_kind": "text",
        "published_at": guess_published_date(normalized, url=final_url),
    }


def score_discovered_url(base_url, url, link_text, include_keywords=None, exclude_keywords=None):
    include_keywords = [item.lower() for item in (include_keywords or DEFAULT_DISCOVERY_KEYWORDS)]
    exclude_keywords = [item.lower() for item in (exclude_keywords or DEFAULT_EXCLUDE_KEYWORDS)]
    decoded_url = urllib.parse.unquote(str(url or ""))
    parsed_url = urllib.parse.urlsplit(decoded_url)
    path_lower = parsed_url.path.lower()
    normalized = f"{decoded_url} {link_text or ''}".lower()
    if not normalized:
        return -999
    if any(keyword in normalized for keyword in exclude_keywords):
        return -999
    if normalized.startswith("javascript:") or normalized.startswith("mailto:"):
        return -999
    if "/sec-filings" in path_lower and not path_lower.endswith((".htm", ".html", ".xml", ".xsd", ".txt", ".pdf")):
        return -999

    score = 0
    for keyword in include_keywords:
        if keyword in normalized:
            score += 3
        if keyword in decoded_url.lower():
            score += 2
    if decoded_url.lower().endswith(".pdf"):
        score += 6
    if same_root_host(base_url, decoded_url):
        score += 2
    if host_key(decoded_url).endswith(PDF_HOST_ALLOWLIST):
        score += 1
    if re.search(r"(fy|q[1-4]|20\d{2})", normalized):
        score += 1
    return score


def discover_links(
    html_text,
    base_url,
    include_keywords=None,
    exclude_keywords=None,
    max_links=12,
    allow_raw_urls=True,
):
    extractor = LinkExtractor(base_url)
    extractor.feed(html_text or "")

    candidates = []
    seen = set()
    for item in extractor.links:
        url = item["url"]
        if url in seen:
            continue
        seen.add(url)
        candidates.append({"url": url, "link_text": item.get("text") or ""})

    if allow_raw_urls:
        for url in extract_raw_urls(html_text):
            if url in seen:
                continue
            seen.add(url)
            candidates.append({"url": url, "link_text": ""})

    ranked = []
    for item in candidates:
        score = score_discovered_url(
            base_url,
            item["url"],
            item.get("link_text"),
            include_keywords=include_keywords,
            exclude_keywords=exclude_keywords,
        )
        if score < 6:
            continue
        ranked.append({**item, "score": score})

    ranked.sort(key=lambda item: (-item["score"], item["url"]))
    return ranked[:max_links]


def fetch_sec_ticker_exchange_map(timeout=30, user_agent=None):
    response = fetch_url(
        "https://www.sec.gov/files/company_tickers_exchange.json",
        timeout=timeout,
        user_agent=user_agent or DEFAULT_SEC_USER_AGENT,
        accept="application/json, text/plain, */*",
    )
    payload = json.loads(response["text"] or "{}")
    fields = payload.get("fields") or []
    positions = {name: index for index, name in enumerate(fields)}
    rows = []
    for item in payload.get("data") or []:
        ticker = str(item[positions["ticker"]] if "ticker" in positions else "").strip().upper()
        if not ticker:
            continue
        rows.append(
            {
                "ticker": ticker,
                "cik": int(item[positions["cik"]]) if "cik" in positions else None,
                "name": str(item[positions["name"]] if "name" in positions else "").strip(),
                "exchange": str(item[positions["exchange"]] if "exchange" in positions else "").strip(),
            }
        )
    return rows


def sec_company_lookup(symbol, timeout=30, user_agent=None):
    wanted = str(symbol or "").strip().upper()
    if not wanted:
        return None
    for row in fetch_sec_ticker_exchange_map(timeout=timeout, user_agent=user_agent):
        if row["ticker"] == wanted:
            return row
    return None


def sec_submissions_url(cik):
    return f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"


def fetch_sec_submissions(cik, timeout=30, user_agent=None):
    response = fetch_url(
        sec_submissions_url(cik),
        timeout=timeout,
        user_agent=user_agent or DEFAULT_SEC_USER_AGENT,
        accept="application/json, text/plain, */*",
    )
    return json.loads(response["text"] or "{}"), response


def list_recent_sec_filings(submissions_payload):
    recent = ((submissions_payload or {}).get("filings") or {}).get("recent") or {}
    forms = recent.get("form") or []
    rows = []
    for index in range(len(forms)):
        row = {}
        for key, values in recent.items():
            if isinstance(values, list) and index < len(values):
                row[key] = values[index]
        if row:
            rows.append(row)
    return rows


def filter_sec_filings(rows, forms=None, days_back=None, limit=None):
    allowed_forms = {item.upper() for item in (forms or []) if str(item).strip()}
    cutoff = None
    if days_back is not None:
        cutoff = (datetime.now().date() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    results = []
    for row in rows or []:
        form = str(row.get("form") or "").strip().upper()
        filing_date = str(row.get("filingDate") or row.get("reportDate") or "").strip()
        if allowed_forms and form not in allowed_forms:
            continue
        if cutoff and filing_date and filing_date < cutoff:
            continue
        results.append(row)
        if limit is not None and len(results) >= limit:
            break
    return results


def sec_index_url(cik, accession_number):
    accession_compact = str(accession_number or "").replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_compact}/index.json"


def sec_document_url(cik, accession_number, name):
    accession_compact = str(accession_number or "").replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_compact}/{name}"


def fetch_sec_index(cik, accession_number, timeout=30, user_agent=None):
    response = fetch_url(
        sec_index_url(cik, accession_number),
        timeout=timeout,
        user_agent=user_agent or DEFAULT_SEC_USER_AGENT,
        accept="application/json, text/plain, */*",
    )
    return json.loads(response["text"] or "{}"), response


def select_sec_material_entries(index_payload, primary_document=None, max_entries=4):
    items = ((index_payload or {}).get("directory") or {}).get("item") or []
    ranked = []
    seen = set()

    def register(name, reason, score):
        if not name or name in seen:
            return
        lower_name = name.lower()
        if lower_name.endswith((".jpg", ".jpeg", ".png", ".gif", ".svg", ".css", ".js", ".xsd", ".xml")):
            return
        if lower_name.endswith(("-index.html", "-index-headers.html")):
            return
        if Path(lower_name).suffix not in {"", ".htm", ".html", ".txt", ".pdf"}:
            return
        seen.add(name)
        ranked.append({"name": name, "reason": reason, "score": score})

    if primary_document:
        register(primary_document, "primary_document", 100)

    for item in items:
        name = str(item.get("name") or "").strip()
        lower_name = name.lower()
        score = 0
        reasons = []
        if "ex99" in lower_name or "99-" in lower_name:
            score += 90
            reasons.append("exhibit_99")
        if any(keyword in lower_name for keyword in ("earnings", "results", "release", "financial")):
            score += 50
            reasons.append("earnings_release")
        if any(keyword in lower_name for keyword in ("presentation", "slides", "deck")):
            score += 45
            reasons.append("presentation")
        if any(keyword in lower_name for keyword in ("transcript", "remarks", "conference", "webcast")):
            score += 45
            reasons.append("call_material")
        if lower_name.endswith(".pdf"):
            score += 8
        if score > 0:
            register(name, "+".join(reasons) or "material", score)

    ranked.sort(key=lambda item: (-item["score"], item["name"]))
    return ranked[:max_entries]


def external_source_id(provider, stable_key):
    return f"external_source__{slugify(provider)}__{slugify(stable_key)[:120]}"
