from __future__ import annotations

import hashlib
import html
import io
import json
import os
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol
from zoneinfo import ZoneInfo

from pdfminer.high_level import extract_text

from smr_app.acquisition.contracts import (
    AcquisitionBatch,
    AcquisitionRequest,
    AuthorityTier,
    EvidenceCandidate,
    NormalizedFact,
    SourceDocument,
    utc_now,
)
from smr_app.research.analysis_v3 import (
    extract_a_share_annual_metrics,
    extract_operating_metrics,
)


CNINFO_QUERY_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
CNINFO_STATIC_ROOT = "https://static.cninfo.com.cn/"
ANNUAL_REPORT_CATEGORY = "category_ndbg_szsh"
PARSER_VERSION = "cninfo-annual-v1"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_IDENTITY_PATH = PROJECT_ROOT / "config" / "cninfo_identities.json"
DEFAULT_CACHE_ROOT = PROJECT_ROOT / "01_data" / "acquisition_raw" / "cninfo"


class CninfoTransport(Protocol):
    def query_announcements(self, form: Mapping[str, str]) -> Mapping[str, Any]: ...

    def fetch_pdf(self, url: str) -> tuple[bytes, str]: ...


class UrllibCninfoTransport:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://www.cninfo.com.cn/",
    }

    def __init__(self, *, timeout_seconds: int = 30) -> None:
        self.timeout_seconds = timeout_seconds

    def query_announcements(self, form: Mapping[str, str]) -> Mapping[str, Any]:
        headers = {**self.headers, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        request = urllib.request.Request(
            CNINFO_QUERY_URL,
            data=urllib.parse.urlencode(dict(form)).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            if response.status != 200:
                raise RuntimeError(f"CNINFO announcement query returned HTTP {response.status}")
            return json.loads(response.read().decode("utf-8", errors="strict"))

    def fetch_pdf(self, url: str) -> tuple[bytes, str]:
        request = urllib.request.Request(url, headers=self.headers)
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            if response.status != 200:
                raise RuntimeError(f"CNINFO PDF download returned HTTP {response.status}")
            return response.read(), str(response.headers.get("Content-Type") or "")


@dataclass(frozen=True)
class CninfoAnnouncement:
    announcement_id: str
    security_code: str
    security_name: str
    title: str
    published_at: str
    adjunct_url: str

    @property
    def pdf_url(self) -> str:
        return urllib.parse.urljoin(CNINFO_STATIC_ROOT, self.adjunct_url)


def _clean_title(value: Any) -> str:
    return re.sub(r"<[^>]+>", "", html.unescape(str(value or ""))).strip()


def _published_at(value: Any) -> str:
    if isinstance(value, (int, float)) and value > 0:
        return datetime.fromtimestamp(value / 1000, tz=ZoneInfo("Asia/Shanghai")).date().isoformat()
    text = str(value or "").strip()
    return text[:10] if text else ""


def _announcement(row: Mapping[str, Any]) -> CninfoAnnouncement | None:
    announcement_id = str(row.get("announcementId") or row.get("announcement_id") or "").strip()
    adjunct_url = str(row.get("adjunctUrl") or row.get("adjunct_url") or "").strip()
    if not announcement_id or not adjunct_url:
        return None
    return CninfoAnnouncement(
        announcement_id=announcement_id,
        security_code=str(row.get("secCode") or row.get("security_code") or "").strip(),
        security_name=str(row.get("secName") or row.get("security_name") or "").strip(),
        title=_clean_title(row.get("announcementTitle") or row.get("title")),
        published_at=_published_at(row.get("announcementTime") or row.get("published_at")),
        adjunct_url=adjunct_url,
    )


def _select_full_annual_report(rows: list[Mapping[str, Any]], security_code: str) -> CninfoAnnouncement | None:
    candidates = []
    for row in rows:
        item = _announcement(row)
        if item is None or item.security_code != security_code:
            continue
        if not re.search(r"20\d{2}年年度报告", item.title):
            continue
        if any(token in item.title for token in ("摘要", "更正", "取消")):
            continue
        candidates.append(item)
    candidates.sort(key=lambda item: (item.published_at, item.announcement_id), reverse=True)
    return candidates[0] if candidates else None


def _pdf_text(raw_pdf: bytes) -> str:
    text = extract_text(io.BytesIO(raw_pdf))
    return text.replace("\x00", "").strip()


def _financial_facts(
    *,
    ticker: str,
    document: SourceDocument,
    annual: Mapping[str, Any],
) -> tuple[NormalizedFact, ...]:
    parsed = extract_a_share_annual_metrics([
        {"chunk_id": document.document_id, "evidence_id": document.document_id, "text": document.raw_text or ""}
    ])
    if parsed.get("status") != "available" or not parsed.get("periods"):
        raise ValueError("annual report main financial table could not be parsed")
    periods = [str(value) for value in parsed["periods"]]
    metrics = parsed["metrics"]
    mapping = {
        "revenue": ("revenue", "CNY"),
        "net_profit_parent": ("attributable_net_income", "CNY"),
        "net_profit_excluding_nonrecurring": ("adjusted_net_income", "CNY"),
        "operating_cash_flow": ("operating_cash_flow", "CNY"),
        "eps": ("basic_eps", "CNY/share"),
        "weighted_roe": ("weighted_roe", "ratio"),
        "total_assets": ("total_assets", "CNY"),
        "attributable_equity": ("attributable_equity", "CNY"),
    }
    output = []
    for field_name, (metric_name, unit) in mapping.items():
        values = metrics.get(metric_name) or {}
        for period in periods:
            value = values.get(period)
            if value is None:
                continue
            output.append(NormalizedFact.build(
                entity_key=ticker,
                data_type="financial_statements",
                field_name=field_name,
                value=value,
                unit=unit,
                period_start=f"{period}-01-01",
                period_end=f"{period}-12-31",
                as_of=f"{period}-12-31",
                source_document_id=document.document_id,
                authority_tier=AuthorityTier.OFFICIAL,
                confidence=0.99,
                metadata={
                    "report_title": document.title,
                    "announcement_id": annual.get("announcement_id"),
                    "parser_version": PARSER_VERSION,
                    "value_scope": "annual",
                },
            ))
    operating = extract_operating_metrics([{
        "chunk_id": document.document_id,
        "evidence_id": document.document_id,
        "chunk_section_type": "operating_results",
        "text": document.raw_text or "",
    }])
    if operating.get("status") == "available":
        gross_margin_values = (
            (periods[0], operating.get("current_gross_margin")),
            (periods[1], operating.get("previous_gross_margin"))
            if len(periods) > 1 else (None, None),
        )
        for period, value in gross_margin_values:
            if not period or value is None:
                continue
            output.append(NormalizedFact.build(
                entity_key=ticker,
                data_type="financial_statements",
                field_name="gross_margin",
                value=value,
                unit="ratio",
                period_start=f"{period}-01-01",
                period_end=f"{period}-12-31",
                as_of=f"{period}-12-31",
                source_document_id=document.document_id,
                authority_tier=AuthorityTier.OFFICIAL,
                confidence=0.99,
                metadata={
                    "report_title": document.title,
                    "announcement_id": annual.get("announcement_id"),
                    "parser_version": PARSER_VERSION,
                    "value_scope": "annual_main_business",
                    "table_layout": operating.get("table_layout"),
                },
            ))
    latest = periods[0]
    present = {item.field_name for item in output if item.as_of == f"{latest}-12-31"}
    missing = set(mapping) - present
    if missing:
        raise ValueError(f"annual report is missing required financial fields: {sorted(missing)}")
    return tuple(output)


def _financial_evidence(
    *, ticker: str, document: SourceDocument, facts: tuple[NormalizedFact, ...]
) -> tuple[EvidenceCandidate, ...]:
    latest_as_of = max(str(item.as_of or "") for item in facts)
    latest = [item for item in facts if item.as_of == latest_as_of]
    labels = {
        "revenue": "营业收入",
        "net_profit_parent": "归母净利润",
        "net_profit_excluding_nonrecurring": "扣非归母净利润",
        "operating_cash_flow": "经营活动现金流量净额",
        "eps": "基本每股收益",
        "weighted_roe": "加权平均净资产收益率",
        "total_assets": "总资产",
        "attributable_equity": "归属于上市公司股东的净资产",
        "gross_margin": "主营业务毛利率",
    }
    candidates = []
    for fact in latest:
        display = f"{fact.value:.4f}" if isinstance(fact.value, float) else str(fact.value)
        candidates.append(EvidenceCandidate.build(
            entity_key=ticker,
            data_type="financial_statements",
            claim_type=fact.field_name,
            text=f"{document.title}披露：{latest_as_of[:4]}年{labels[fact.field_name]}为 {display} {fact.unit or ''}。",
            source_document_ids=(document.document_id,),
            authority_tier=AuthorityTier.OFFICIAL,
            occurred_at=document.published_at,
            usable_for=("research", "analysis", "promotion_evidence"),
            status="validated",
            metadata={"fact_id": fact.fact_id, "source_url": document.source_url},
        ))
    return tuple(candidates)


class CninfoOfficialProvider:
    provider_id = "cninfo_official"
    priority = 10
    authority_tier = AuthorityTier.OFFICIAL
    data_types = frozenset({"official_filings", "financial_statements"})
    markets = frozenset({"A", "CN"})

    def __init__(
        self,
        *,
        cache_root: str | Path = DEFAULT_CACHE_ROOT,
        identity_path: str | Path = DEFAULT_IDENTITY_PATH,
        transport: CninfoTransport | None = None,
        text_extractor: Callable[[bytes], str] = _pdf_text,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.cache_root = Path(cache_root)
        self.identity_path = Path(identity_path)
        self.transport = transport or UrllibCninfoTransport()
        self.text_extractor = text_extractor
        self.clock = clock

    def _identity(self, ticker: str) -> dict[str, Any]:
        payload = json.loads(self.identity_path.read_text(encoding="utf-8"))
        identity = dict((payload.get("identities") or {}).get(ticker) or {})
        required = {"security_code", "security_name", "org_id", "plate", "column"}
        missing = sorted(required - {key for key, value in identity.items() if value})
        if missing:
            raise ValueError(f"CNINFO identity unresolved for {ticker}: missing {missing}")
        return identity

    @staticmethod
    def _query_form(identity: Mapping[str, Any], now: datetime) -> dict[str, str]:
        return {
            "pageNum": "1",
            "pageSize": "30",
            "column": str(identity["column"]),
            "tabName": "fulltext",
            "plate": str(identity["plate"]),
            "stock": f"{identity['security_code']},{identity['org_id']}",
            "searchkey": "",
            "secid": "",
            "category": ANNUAL_REPORT_CATEGORY,
            "trade": "",
            "seDate": f"{now.year - 3}-01-01~{now.date().isoformat()}",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "true",
        }

    def _latest_annual(self, identity: Mapping[str, Any], now: datetime) -> tuple[CninfoAnnouncement, dict[str, Any]]:
        query_error = None
        rows: list[Mapping[str, Any]] = []
        try:
            payload = self.transport.query_announcements(self._query_form(identity, now))
            rows = list(payload.get("announcements") or [])
        except Exception as exc:
            query_error = f"{type(exc).__name__}: {exc}"[:500]
        selected = _select_full_annual_report(rows, str(identity["security_code"]))
        verified = _announcement({
            **dict(identity.get("known_annual_report") or {}),
            "secCode": identity["security_code"],
            "secName": identity["security_name"],
        })
        if selected and verified:
            if (verified.published_at, verified.announcement_id) > (
                selected.published_at,
                selected.announcement_id,
            ):
                return verified, {
                    "source": "verified_manifest_preferred",
                    "query_error": query_error,
                    "result_count": len(rows),
                    "live_announcement_id": selected.announcement_id,
                }
            return selected, {
                "source": "live_index",
                "query_error": query_error,
                "result_count": len(rows),
            }
        if selected:
            return selected, {"source": "live_index", "query_error": query_error, "result_count": len(rows)}
        if verified is None:
            raise RuntimeError(f"CNINFO annual report not found; live query error={query_error!r}")
        return verified, {
            "source": "verified_manifest_fallback",
            "query_error": query_error,
            "result_count": len(rows),
        }

    def _raw_path(self, ticker: str, announcement_id: str) -> Path:
        root = self.cache_root.resolve()
        target = (root / ticker.replace(".", "_") / f"{announcement_id}.pdf").resolve()
        if root != target and root not in target.parents:
            raise ValueError("raw cache path escaped configured root")
        return target

    def _load_pdf(self, ticker: str, item: CninfoAnnouncement) -> tuple[bytes, str, Path, bool]:
        path = self._raw_path(ticker, item.announcement_id)
        from_cache = path.exists()
        if from_cache:
            raw = path.read_bytes()
            content_type = "application/pdf"
        else:
            raw, content_type = self.transport.fetch_pdf(item.pdf_url)
        if len(raw) < 1024 or not raw.lstrip().startswith(b"%PDF"):
            raise ValueError("CNINFO raw document failed PDF signature/size validation")
        if content_type and "pdf" not in content_type.lower() and "octet-stream" not in content_type.lower():
            raise ValueError(f"CNINFO raw document has unexpected content type: {content_type}")
        if not from_cache:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        return raw, content_type, path, from_cache

    def acquire(self, request: AcquisitionRequest) -> AcquisitionBatch:
        requirement = request.requirement
        if requirement.data_type not in self.data_types or requirement.market not in self.markets:
            raise ValueError("CNINFO provider does not support this requirement")
        now = self.clock()
        identity = self._identity(requirement.entity_key)
        annual, index_meta = self._latest_annual(identity, now)
        raw_pdf, content_type, raw_path, from_cache = self._load_pdf(requirement.entity_key, annual)
        raw_text = self.text_extractor(raw_pdf)
        if len(raw_text) < 5_000:
            raise ValueError("CNINFO PDF text extraction produced insufficient content")
        pdf_sha256 = hashlib.sha256(raw_pdf).hexdigest()
        document = SourceDocument.build(
            source_id=f"cninfo:{annual.announcement_id}",
            entity_key=requirement.entity_key,
            data_type=requirement.data_type,
            source_type="annual_report",
            authority_tier=AuthorityTier.OFFICIAL,
            title=annual.title,
            fetched_at=now,
            source_url=annual.pdf_url,
            published_at=annual.published_at,
            raw_text=raw_text,
            raw_payload={
                "announcement_id": annual.announcement_id,
                "security_code": annual.security_code,
                "security_name": annual.security_name,
                "adjunct_url": annual.adjunct_url,
                "index": index_meta,
            },
            parser_version=PARSER_VERSION,
            metadata={
                "raw_file_path": str(raw_path),
                "raw_sha256": pdf_sha256,
                "raw_size_bytes": len(raw_pdf),
                "content_type": content_type,
                "raw_cache_hit": from_cache,
                "official_index_url": CNINFO_QUERY_URL,
            },
        )
        if requirement.data_type == "official_filings":
            candidate = EvidenceCandidate.build(
                entity_key=requirement.entity_key,
                data_type="official_filings",
                claim_type="official_annual_report",
                text=f"巨潮资讯已披露《{annual.title}》（公告日期 {annual.published_at}）。",
                source_document_ids=(document.document_id,),
                authority_tier=AuthorityTier.OFFICIAL,
                occurred_at=annual.published_at,
                usable_for=("research", "analysis"),
                status="validated",
                metadata={"source_url": annual.pdf_url, "announcement_id": annual.announcement_id},
            )
            return AcquisitionBatch(
                documents=(document,),
                evidence_candidates=(candidate,),
                available_through=annual.published_at,
                required_fields_present=("announcement_index", "raw_document", "full_text"),
                quality_status="verified",
                is_complete=True,
                metadata={"announcement_id": annual.announcement_id, "index_source": index_meta["source"]},
            )
        facts = _financial_facts(
            ticker=requirement.entity_key,
            document=document,
            annual={"announcement_id": annual.announcement_id},
        )
        candidates = _financial_evidence(ticker=requirement.entity_key, document=document, facts=facts)
        latest_period = max(str(item.as_of or "") for item in facts)
        present = tuple(sorted({item.field_name for item in facts if item.as_of == latest_period}))
        return AcquisitionBatch(
            documents=(document,),
            facts=facts,
            evidence_candidates=candidates,
            available_through=latest_period,
            required_fields_present=present,
            quality_status="verified",
            is_complete=set(requirement.required_fields).issubset(present),
            metadata={
                "announcement_id": annual.announcement_id,
                "index_source": index_meta["source"],
                "periods": sorted({str(item.as_of)[:4] for item in facts}, reverse=True),
            },
        )


def default_cninfo_provider() -> CninfoOfficialProvider:
    configured = os.environ.get("SMR_ACQUISITION_RAW_ROOT")
    cache_root = Path(configured) / "cninfo" if configured else DEFAULT_CACHE_ROOT
    return CninfoOfficialProvider(cache_root=cache_root)
