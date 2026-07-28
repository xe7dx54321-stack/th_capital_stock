from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Mapping, Protocol


class AcquisitionMode(str, Enum):
    CACHE_ONLY = "cache_only"
    REFRESH_IF_STALE = "refresh_if_stale"
    FORCE_REFRESH = "force_refresh"


class AuthorityTier(str, Enum):
    PRIMARY = "primary"
    OFFICIAL = "official"
    REPUTABLE_SECONDARY = "reputable_secondary"
    DISCOVERY = "discovery"


AUTHORITY_RANK = {
    AuthorityTier.DISCOVERY: 1,
    AuthorityTier.REPUTABLE_SECONDARY: 2,
    AuthorityTier.OFFICIAL: 3,
    AuthorityTier.PRIMARY: 4,
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(encoded).hexdigest()[:24]}"


def _iso(value: datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


@dataclass(frozen=True)
class DataRequirement:
    entity_key: str
    data_type: str
    market: str
    as_of: str | None = None
    required_fields: tuple[str, ...] = ()
    maximum_age: timedelta | None = None
    minimum_authority: AuthorityTier = AuthorityTier.DISCOVERY
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.entity_key.strip():
            raise ValueError("entity_key is required")
        if not self.data_type.strip():
            raise ValueError("data_type is required")
        if not self.market.strip():
            raise ValueError("market is required")
        if self.maximum_age is not None and self.maximum_age.total_seconds() < 0:
            raise ValueError("maximum_age cannot be negative")
        object.__setattr__(self, "required_fields", tuple(dict.fromkeys(self.required_fields)))


@dataclass(frozen=True)
class AcquisitionRequest:
    request_id: str
    requirement: DataRequirement
    mode: AcquisitionMode
    workflow_run_id: str | None
    created_at: str

    @classmethod
    def create(
        cls,
        requirement: DataRequirement,
        mode: AcquisitionMode,
        workflow_run_id: str | None,
        now: datetime,
    ) -> "AcquisitionRequest":
        return cls(
            request_id=f"acqreq_{uuid.uuid4().hex}",
            requirement=requirement,
            mode=mode,
            workflow_run_id=workflow_run_id,
            created_at=_iso(now) or "",
        )


@dataclass(frozen=True)
class SourceDocument:
    document_id: str
    source_id: str
    entity_key: str
    data_type: str
    source_type: str
    authority_tier: AuthorityTier
    source_url: str | None
    title: str
    published_at: str | None
    fetched_at: str
    content_hash: str
    raw_text: str | None = None
    raw_payload: Mapping[str, Any] = field(default_factory=dict)
    parser_version: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def build(
        cls,
        *,
        source_id: str,
        entity_key: str,
        data_type: str,
        source_type: str,
        authority_tier: AuthorityTier,
        title: str,
        fetched_at: datetime | str,
        source_url: str | None = None,
        published_at: datetime | str | None = None,
        raw_text: str | None = None,
        raw_payload: Mapping[str, Any] | None = None,
        parser_version: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "SourceDocument":
        payload = dict(raw_payload or {})
        content_bytes = (raw_text or json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)).encode("utf-8")
        content_hash = hashlib.sha256(content_bytes).hexdigest()
        identity = {
            "source_id": source_id,
            "entity_key": entity_key,
            "data_type": data_type,
            "source_url": source_url,
            "published_at": _iso(published_at),
            "content_hash": content_hash,
        }
        return cls(
            document_id=_stable_id("srcdoc", identity),
            source_id=source_id,
            entity_key=entity_key,
            data_type=data_type,
            source_type=source_type,
            authority_tier=authority_tier,
            source_url=source_url,
            title=title,
            published_at=_iso(published_at),
            fetched_at=_iso(fetched_at) or "",
            content_hash=content_hash,
            raw_text=raw_text,
            raw_payload=payload,
            parser_version=parser_version,
            metadata=dict(metadata or {}),
        )


@dataclass(frozen=True)
class NormalizedFact:
    fact_id: str
    entity_key: str
    data_type: str
    field_name: str
    value: Any
    unit: str | None
    period_start: str | None
    period_end: str | None
    as_of: str | None
    source_document_id: str
    authority_tier: AuthorityTier
    verification_status: str = "verified"
    confidence: float = 1.0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def build(
        cls,
        *,
        entity_key: str,
        data_type: str,
        field_name: str,
        value: Any,
        source_document_id: str,
        authority_tier: AuthorityTier,
        unit: str | None = None,
        period_start: str | None = None,
        period_end: str | None = None,
        as_of: str | None = None,
        verification_status: str = "verified",
        confidence: float = 1.0,
        metadata: Mapping[str, Any] | None = None,
    ) -> "NormalizedFact":
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        identity = {
            "entity_key": entity_key,
            "data_type": data_type,
            "field_name": field_name,
            "value": value,
            "unit": unit,
            "period_start": period_start,
            "period_end": period_end,
            "as_of": as_of,
            "source_document_id": source_document_id,
        }
        return cls(
            fact_id=_stable_id("fact", identity),
            entity_key=entity_key,
            data_type=data_type,
            field_name=field_name,
            value=value,
            unit=unit,
            period_start=period_start,
            period_end=period_end,
            as_of=as_of,
            source_document_id=source_document_id,
            authority_tier=authority_tier,
            verification_status=verification_status,
            confidence=confidence,
            metadata=dict(metadata or {}),
        )


@dataclass(frozen=True)
class EvidenceCandidate:
    candidate_id: str
    entity_key: str
    data_type: str
    claim_type: str
    text: str
    source_document_ids: tuple[str, ...]
    authority_tier: AuthorityTier
    occurred_at: str | None = None
    usable_for: tuple[str, ...] = ()
    status: str = "pending_validation"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def build(
        cls,
        *,
        entity_key: str,
        data_type: str,
        claim_type: str,
        text: str,
        source_document_ids: tuple[str, ...],
        authority_tier: AuthorityTier,
        occurred_at: str | None = None,
        usable_for: tuple[str, ...] = (),
        status: str = "pending_validation",
        metadata: Mapping[str, Any] | None = None,
    ) -> "EvidenceCandidate":
        document_ids = tuple(dict.fromkeys(source_document_ids))
        if not document_ids:
            raise ValueError("evidence candidate requires at least one source document")
        identity = {
            "entity_key": entity_key,
            "data_type": data_type,
            "claim_type": claim_type,
            "text": text,
            "source_document_ids": document_ids,
            "occurred_at": occurred_at,
        }
        return cls(
            candidate_id=_stable_id("evcand", identity),
            entity_key=entity_key,
            data_type=data_type,
            claim_type=claim_type,
            text=" ".join(text.split()),
            source_document_ids=document_ids,
            authority_tier=authority_tier,
            occurred_at=occurred_at,
            usable_for=tuple(dict.fromkeys(usable_for)),
            status=status,
            metadata=dict(metadata or {}),
        )


@dataclass(frozen=True)
class DatasetState:
    entity_key: str
    data_type: str
    market: str
    available_through: str | None
    last_checked_at: str
    last_successful_fetch_at: str | None
    required_fields_present: tuple[str, ...] = ()
    quality_status: str = "unknown"
    is_complete: bool = False
    source_ids: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def satisfies(self, requirement: DataRequirement, now: datetime) -> bool:
        if not self.is_complete or self.quality_status not in {"verified", "usable", "cross_validated"}:
            return False
        if requirement.as_of and (not self.available_through or self.available_through < requirement.as_of):
            return False
        if not set(requirement.required_fields).issubset(self.required_fields_present):
            return False
        if requirement.maximum_age is not None:
            if not self.last_successful_fetch_at:
                return False
            fetched_at = datetime.fromisoformat(self.last_successful_fetch_at.replace("Z", "+00:00"))
            if fetched_at.tzinfo is None:
                fetched_at = fetched_at.replace(tzinfo=timezone.utc)
            if now.astimezone(timezone.utc) - fetched_at.astimezone(timezone.utc) > requirement.maximum_age:
                return False
        return True


@dataclass(frozen=True)
class AcquisitionBatch:
    documents: tuple[SourceDocument, ...] = ()
    facts: tuple[NormalizedFact, ...] = ()
    evidence_candidates: tuple[EvidenceCandidate, ...] = ()
    available_through: str | None = None
    required_fields_present: tuple[str, ...] = ()
    quality_status: str = "unknown"
    is_complete: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AcquisitionResult:
    request_id: str
    status: str
    provider_id: str | None = None
    persisted_documents: int = 0
    persisted_facts: int = 0
    persisted_evidence_candidates: int = 0
    dataset_state: DatasetState | None = None
    errors: tuple[Mapping[str, Any], ...] = ()


class AcquisitionProvider(Protocol):
    provider_id: str
    priority: int
    authority_tier: AuthorityTier
    data_types: frozenset[str]
    markets: frozenset[str]

    def acquire(self, request: AcquisitionRequest) -> AcquisitionBatch:
        ...


def authority_meets(actual: AuthorityTier, minimum: AuthorityTier) -> bool:
    return AUTHORITY_RANK[actual] >= AUTHORITY_RANK[minimum]
