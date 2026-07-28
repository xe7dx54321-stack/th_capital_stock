from __future__ import annotations

from datetime import datetime
from typing import Iterable

from .contracts import (
    AcquisitionBatch,
    AcquisitionMode,
    AcquisitionProvider,
    AcquisitionRequest,
    AcquisitionResult,
    DataRequirement,
    authority_meets,
    utc_now,
)
from .store import AcquisitionStore


class AcquisitionKernel:
    def __init__(
        self,
        store: AcquisitionStore,
        providers: Iterable[AcquisitionProvider],
        *,
        clock=utc_now,
    ) -> None:
        self.store = store
        self.providers = tuple(providers)
        self.clock = clock

    def _eligible_providers(self, requirement: DataRequirement) -> list[AcquisitionProvider]:
        return sorted(
            (
                provider
                for provider in self.providers
                if requirement.data_type in provider.data_types
                and (not provider.markets or requirement.market in provider.markets)
                and authority_meets(provider.authority_tier, requirement.minimum_authority)
            ),
            key=lambda provider: (provider.priority, provider.provider_id),
        )

    @staticmethod
    def _validate_batch(requirement: DataRequirement, batch: AcquisitionBatch) -> None:
        if not isinstance(batch, AcquisitionBatch):
            raise TypeError("provider must return AcquisitionBatch")
        for document in batch.documents:
            if document.entity_key != requirement.entity_key or document.data_type != requirement.data_type:
                raise ValueError("source document does not match the data requirement")
            if not authority_meets(document.authority_tier, requirement.minimum_authority):
                raise ValueError("source document authority is below the requirement")
            if not document.raw_text and not document.raw_payload:
                raise ValueError("source document must preserve raw text or raw payload")
        for fact in batch.facts:
            if fact.entity_key != requirement.entity_key or fact.data_type != requirement.data_type:
                raise ValueError("normalized fact does not match the data requirement")
            if not authority_meets(fact.authority_tier, requirement.minimum_authority):
                raise ValueError("normalized fact authority is below the requirement")
        for candidate in batch.evidence_candidates:
            if candidate.entity_key != requirement.entity_key or candidate.data_type != requirement.data_type:
                raise ValueError("evidence candidate does not match the data requirement")
            if not authority_meets(candidate.authority_tier, requirement.minimum_authority):
                raise ValueError("evidence candidate authority is below the requirement")

    def acquire(
        self,
        requirement: DataRequirement,
        *,
        mode: AcquisitionMode = AcquisitionMode.REFRESH_IF_STALE,
        workflow_run_id: str | None = None,
    ) -> AcquisitionResult:
        if isinstance(mode, str):
            mode = AcquisitionMode(mode)
        now: datetime = self.clock()
        request = AcquisitionRequest.create(requirement, mode, workflow_run_id, now)
        self.store.create_request(request)
        existing = self.store.get_dataset_state(requirement)

        if mode is not AcquisitionMode.FORCE_REFRESH and existing and existing.satisfies(requirement, now):
            completed_at = now.isoformat()
            self.store.finish_request(request.request_id, "cache_hit", completed_at, {"cache": "fresh"})
            return AcquisitionResult(request_id=request.request_id, status="cache_hit", dataset_state=existing)

        if mode is AcquisitionMode.CACHE_ONLY:
            completed_at = now.isoformat()
            self.store.finish_request(request.request_id, "cache_miss", completed_at, {"cache": "missing_or_stale"})
            return AcquisitionResult(request_id=request.request_id, status="cache_miss", dataset_state=existing)

        errors: list[dict[str, str]] = []
        total_documents = 0
        total_facts = 0
        total_candidates = 0
        latest_state = existing
        latest_provider: str | None = None
        total_conflicts = 0

        providers = self._eligible_providers(requirement)
        if not providers:
            completed_at = self.clock().isoformat()
            self.store.finish_request(
                request.request_id,
                "failed",
                completed_at,
                {"reason": "no_eligible_provider"},
            )
            return AcquisitionResult(
                request_id=request.request_id,
                status="failed",
                dataset_state=existing,
                errors=({"error_code": "NoEligibleProvider", "message": "no eligible acquisition provider"},),
            )

        for provider in providers:
            started_at = self.clock().isoformat()
            run_id = self.store.start_run(request.request_id, provider.provider_id, started_at)
            try:
                batch = provider.acquire(request)
                self._validate_batch(requirement, batch)
                completed_at = self.clock().isoformat()
                documents, facts, candidates, latest_state, conflicts = self.store.persist_batch(
                    request,
                    provider.provider_id,
                    batch,
                    completed_at,
                )
                total_documents += documents
                total_facts += facts
                total_candidates += candidates
                total_conflicts += conflicts
                latest_provider = provider.provider_id
                self.store.finish_run(
                    run_id,
                    status="completed",
                    completed_at=completed_at,
                    summary={
                        "documents": documents,
                        "facts": facts,
                        "evidence_candidates": candidates,
                        "conflicts": conflicts,
                        "is_complete": latest_state.is_complete,
                    },
                )
                if latest_state.satisfies(requirement, self.clock()) or conflicts:
                    status = "acquired_with_conflicts" if total_conflicts else "acquired"
                    self.store.finish_request(
                        request.request_id,
                        status,
                        completed_at,
                        {"provider_id": latest_provider, "conflicts": total_conflicts},
                    )
                    return AcquisitionResult(
                        request_id=request.request_id,
                        status=status,
                        provider_id=latest_provider,
                        persisted_documents=total_documents,
                        persisted_facts=total_facts,
                        persisted_evidence_candidates=total_candidates,
                        dataset_state=latest_state,
                        errors=tuple(errors),
                    )
            except Exception as exc:
                completed_at = self.clock().isoformat()
                self.store.finish_run(run_id, status="failed", completed_at=completed_at, error=exc)
                errors.append(
                    {
                        "provider_id": provider.provider_id,
                        "error_code": type(exc).__name__,
                        "message": str(exc)[:500],
                    }
                )

        completed_at = self.clock().isoformat()
        status = "partial" if latest_state is not None and total_documents + total_facts + total_candidates > 0 else "failed"
        self.store.finish_request(
            request.request_id,
            status,
            completed_at,
            {"provider_id": latest_provider, "errors": errors},
        )
        return AcquisitionResult(
            request_id=request.request_id,
            status=status,
            provider_id=latest_provider,
            persisted_documents=total_documents,
            persisted_facts=total_facts,
            persisted_evidence_candidates=total_candidates,
            dataset_state=latest_state,
            errors=tuple(errors),
        )
