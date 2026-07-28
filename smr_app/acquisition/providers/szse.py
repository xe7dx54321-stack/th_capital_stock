from __future__ import annotations

import hashlib
import io
import json
import math
import os
import re
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from pdfminer.high_level import extract_text

from smr_app.acquisition.contracts import (
    AcquisitionBatch,
    AcquisitionRequest,
    AuthorityTier,
    EvidenceCandidate,
    SourceDocument,
    utc_now,
)
from smr_app.acquisition.providers.cninfo import PARSER_VERSION, _financial_evidence, _financial_facts


SZSE_QUERY_URL = "https://www.szse.cn/api/disc/announcement/annList"
SZSE_DOWNLOAD_ROOT = "https://disc.static.szse.cn/download"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CACHE_ROOT = PROJECT_ROOT / "01_data" / "acquisition_raw" / "szse"


class SzseTransport(Protocol):
    def query_announcements(self, payload: Mapping[str, Any]) -> Mapping[str, Any]: ...

    def fetch_pdf(self, url: str) -> tuple[bytes, str]: ...


class UrllibSzseTransport:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://www.szse.cn/disclosure/listed/notice/index.html",
    }

    def __init__(self, *, timeout_seconds: int = 30) -> None:
        self.timeout_seconds = timeout_seconds

    def query_announcements(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        request = urllib.request.Request(
            SZSE_QUERY_URL,
            data=json.dumps(dict(payload), ensure_ascii=False).encode("utf-8"),
            headers={**self.headers, "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            if response.status != 200:
                raise RuntimeError(f"SZSE announcement query returned HTTP {response.status}")
            return json.loads(response.read().decode("utf-8", errors="strict"))

    def fetch_pdf(self, url: str) -> tuple[bytes, str]:
        request = urllib.request.Request(url, headers={**self.headers, "Accept": "application/pdf,*/*"})
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            if response.status != 200:
                raise RuntimeError(f"SZSE PDF download returned HTTP {response.status}")
            return response.read(), str(response.headers.get("Content-Type") or "")


def _pdf_text(raw_pdf: bytes) -> str:
    return extract_text(io.BytesIO(raw_pdf)).replace("\x00", "").strip()


def _select_annual(rows: list[Mapping[str, Any]], code: str) -> dict[str, str] | None:
    candidates = []
    for row in rows:
        codes = [str(value) for value in row.get("secCode") or []]
        title = str(row.get("title") or "").strip()
        if code not in codes or not re.search(r"20\d{2}年年度报告$", title):
            continue
        if any(token in title for token in ("摘要", "更正", "取消")):
            continue
        ann_id = str(row.get("annId") or "").strip()
        attach_path = str(row.get("attachPath") or "").strip()
        if not ann_id or not attach_path:
            continue
        candidates.append({
            "announcement_id": ann_id,
            "title": title.split("：", 1)[-1],
            "security_name": title.split("：", 1)[0] if "：" in title else "",
            "published_at": str(row.get("publishTime") or "")[:10],
            "attach_path": attach_path,
            "pdf_url": SZSE_DOWNLOAD_ROOT + (attach_path if attach_path.startswith("/") else "/" + attach_path),
        })
    candidates.sort(key=lambda item: (item["published_at"], item["announcement_id"]), reverse=True)
    return candidates[0] if candidates else None


class SzseOfficialProvider:
    provider_id = "szse_official"
    priority = 20
    authority_tier = AuthorityTier.OFFICIAL
    data_types = frozenset({"official_filings", "financial_statements"})
    markets = frozenset({"A", "CN"})

    def __init__(
        self,
        *,
        cache_root: str | Path = DEFAULT_CACHE_ROOT,
        transport: SzseTransport | None = None,
        text_extractor: Callable[[bytes], str] = _pdf_text,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.cache_root = Path(cache_root)
        self.transport = transport or UrllibSzseTransport()
        self.text_extractor = text_extractor
        self.clock = clock

    def _raw_path(self, ticker: str, announcement_id: str) -> Path:
        root = self.cache_root.resolve()
        target = (root / ticker.replace(".", "_") / f"{announcement_id}.pdf").resolve()
        if root != target and root not in target.parents:
            raise ValueError("raw cache path escaped configured root")
        return target

    def acquire(self, request: AcquisitionRequest) -> AcquisitionBatch:
        requirement = request.requirement
        ticker = requirement.entity_key
        if requirement.data_type not in self.data_types or requirement.market not in self.markets:
            raise ValueError("SZSE provider does not support this requirement")
        if not ticker.endswith(".SZ"):
            raise ValueError("SZSE provider only supports Shenzhen-listed securities")
        now = self.clock()
        code = ticker.split(".", 1)[0]
        payload = {
            "seDate": [f"{now.year - 1}-01-01", now.date().isoformat()],
            "stock": [code],
            "channelCode": ["listedNotice_disc"],
            "pageNum": 1,
            "pageSize": 30,
        }
        response = self.transport.query_announcements(payload)
        rows = list(response.get("data") or [])
        annual = _select_annual(rows, code)
        total = int(response.get("announceCount") or len(rows))
        page_count = min(10, max(1, math.ceil(total / int(payload["pageSize"]))))
        for page_number in range(2, page_count + 1):
            if annual is not None:
                break
            payload["pageNum"] = page_number
            page = self.transport.query_announcements(payload)
            page_rows = list(page.get("data") or [])
            rows.extend(page_rows)
            annual = _select_annual(page_rows, code)
        if annual is None:
            sample_titles = [str(item.get("title") or "") for item in rows[:5]]
            raise RuntimeError(
                f"SZSE annual report not found for {ticker}; keys={sorted(response.keys())}; "
                f"data_count={len(rows)}; sample_titles={sample_titles}"
            )
        path = self._raw_path(ticker, annual["announcement_id"])
        from_cache = path.exists()
        if from_cache:
            raw_pdf, content_type = path.read_bytes(), "application/pdf"
        else:
            raw_pdf, content_type = self.transport.fetch_pdf(annual["pdf_url"])
        if len(raw_pdf) < 1024 or not raw_pdf.lstrip().startswith(b"%PDF"):
            raise ValueError("SZSE raw document failed PDF signature/size validation")
        if content_type and "pdf" not in content_type.lower() and "octet-stream" not in content_type.lower():
            raise ValueError(f"SZSE raw document has unexpected content type: {content_type}")
        if not from_cache:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw_pdf)
        raw_text = self.text_extractor(raw_pdf)
        if len(raw_text) < 5_000:
            raise ValueError("SZSE PDF text extraction produced insufficient content")
        document = SourceDocument.build(
            source_id=f"szse:{annual['announcement_id']}",
            entity_key=ticker,
            data_type=requirement.data_type,
            source_type="annual_report",
            authority_tier=AuthorityTier.OFFICIAL,
            title=annual["title"],
            fetched_at=now,
            source_url=annual["pdf_url"],
            published_at=annual["published_at"],
            raw_text=raw_text,
            raw_payload={
                "announcement_id": annual["announcement_id"],
                "security_code": code,
                "security_name": annual["security_name"],
                "attach_path": annual["attach_path"],
                "index_result_count": len(rows),
            },
            parser_version="szse-" + PARSER_VERSION,
            metadata={
                "raw_file_path": str(path),
                "raw_sha256": hashlib.sha256(raw_pdf).hexdigest(),
                "raw_size_bytes": len(raw_pdf),
                "content_type": content_type,
                "raw_cache_hit": from_cache,
                "official_index_url": SZSE_QUERY_URL,
            },
        )
        if requirement.data_type == "official_filings":
            candidate = EvidenceCandidate.build(
                entity_key=ticker,
                data_type="official_filings",
                claim_type="official_annual_report",
                text=f"深圳证券交易所已披露《{annual['title']}》（公告日期 {annual['published_at']}）。",
                source_document_ids=(document.document_id,),
                authority_tier=AuthorityTier.OFFICIAL,
                occurred_at=annual["published_at"],
                usable_for=("research", "analysis"),
                status="validated",
                metadata={"source_url": annual["pdf_url"], "announcement_id": annual["announcement_id"]},
            )
            return AcquisitionBatch(
                documents=(document,), evidence_candidates=(candidate,),
                available_through=annual["published_at"],
                required_fields_present=("announcement_index", "raw_document", "full_text"),
                quality_status="verified", is_complete=True,
                metadata={"announcement_id": annual["announcement_id"], "index_source": "szse_live_index"},
            )
        facts = _financial_facts(
            ticker=ticker, document=document, annual={"announcement_id": annual["announcement_id"]}
        )
        candidates = _financial_evidence(ticker=ticker, document=document, facts=facts)
        latest_period = max(str(item.as_of or "") for item in facts)
        present = tuple(sorted({item.field_name for item in facts if item.as_of == latest_period}))
        return AcquisitionBatch(
            documents=(document,), facts=facts, evidence_candidates=candidates,
            available_through=latest_period, required_fields_present=present,
            quality_status="verified", is_complete=set(requirement.required_fields).issubset(present),
            metadata={
                "announcement_id": annual["announcement_id"], "index_source": "szse_live_index",
                "periods": sorted({str(item.as_of)[:4] for item in facts}, reverse=True),
            },
        )


def default_szse_provider() -> SzseOfficialProvider:
    configured = os.environ.get("SMR_ACQUISITION_RAW_ROOT")
    cache_root = Path(configured) / "szse" if configured else DEFAULT_CACHE_ROOT
    return SzseOfficialProvider(cache_root=cache_root)
