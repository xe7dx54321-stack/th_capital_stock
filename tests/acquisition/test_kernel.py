from __future__ import annotations

import sqlite3
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from smr_app.acquisition.contracts import (
    AcquisitionBatch,
    AcquisitionMode,
    AuthorityTier,
    DataRequirement,
    DatasetState,
    EvidenceCandidate,
    NormalizedFact,
    SourceDocument,
)
from smr_app.acquisition.kernel import AcquisitionKernel
from smr_app.acquisition.store import AcquisitionStore
from smr_app.runtime.migrations import apply_migrations


UTC = timezone.utc


class FakeProvider:
    def __init__(
        self,
        provider_id: str,
        *,
        priority: int = 100,
        authority_tier: AuthorityTier = AuthorityTier.OFFICIAL,
        error: Exception | None = None,
    ) -> None:
        self.provider_id = provider_id
        self.priority = priority
        self.authority_tier = authority_tier
        self.data_types = frozenset({"financial_statements"})
        self.markets = frozenset({"A"})
        self.error = error
        self.calls = 0

    def acquire(self, request):
        self.calls += 1
        if self.error:
            raise self.error
        document = SourceDocument.build(
            source_id=self.provider_id,
            entity_key=request.requirement.entity_key,
            data_type=request.requirement.data_type,
            source_type="exchange_filing",
            authority_tier=self.authority_tier,
            source_url="https://example.test/annual-report.pdf",
            title="2025 年年度报告",
            published_at="2026-03-31T00:00:00+00:00",
            fetched_at="2026-07-22T02:00:00+00:00",
            raw_text="营业收入 382.40 亿元；归母净利润 107.97 亿元。",
        )
        fact = NormalizedFact.build(
            entity_key=request.requirement.entity_key,
            data_type=request.requirement.data_type,
            field_name="net_profit_parent",
            value=10_797_000_000,
            unit="CNY",
            as_of="2025-12-31",
            source_document_id=document.document_id,
            authority_tier=self.authority_tier,
            confidence=0.99,
        )
        candidate = EvidenceCandidate.build(
            entity_key=request.requirement.entity_key,
            data_type=request.requirement.data_type,
            claim_type="financial_fact",
            text="2025 年归母净利润为 107.97 亿元。",
            source_document_ids=(document.document_id,),
            authority_tier=self.authority_tier,
            occurred_at="2025-12-31",
        )
        return AcquisitionBatch(
            documents=(document,),
            facts=(fact,),
            evidence_candidates=(candidate,),
            available_through="2025-12-31",
            required_fields_present=("net_profit_parent",),
            quality_status="verified",
        )


class AcquisitionKernelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "control.db"
        apply_migrations(self.db_path)
        self.store = AcquisitionStore(self.db_path)
        self.now = datetime(2026, 7, 22, 3, 0, tzinfo=UTC)
        self.requirement = DataRequirement(
            entity_key="300308.SZ",
            data_type="financial_statements",
            market="A",
            as_of="2025-12-31",
            required_fields=("net_profit_parent",),
            maximum_age=timedelta(days=180),
            minimum_authority=AuthorityTier.OFFICIAL,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_cache_only_never_calls_provider_when_cache_is_missing(self) -> None:
        provider = FakeProvider("cninfo")
        kernel = AcquisitionKernel(self.store, [provider], clock=lambda: self.now)

        result = kernel.acquire(self.requirement, mode=AcquisitionMode.CACHE_ONLY)

        self.assertEqual("cache_miss", result.status)
        self.assertEqual(0, provider.calls)
        self.assertEqual([], self.store.list_runs(result.request_id))

    def test_refresh_if_stale_reuses_fresh_complete_dataset(self) -> None:
        self.store.upsert_dataset_state(
            DatasetState(
                entity_key="300308.SZ",
                data_type="financial_statements",
                market="A",
                available_through="2025-12-31",
                last_checked_at=(self.now - timedelta(minutes=10)).isoformat(),
                last_successful_fetch_at=(self.now - timedelta(minutes=10)).isoformat(),
                required_fields_present=("net_profit_parent",),
                quality_status="verified",
                is_complete=True,
                source_ids=("cninfo",),
            )
        )
        provider = FakeProvider("cninfo")
        kernel = AcquisitionKernel(self.store, [provider], clock=lambda: self.now)

        result = kernel.acquire(self.requirement, mode=AcquisitionMode.REFRESH_IF_STALE)

        self.assertEqual("cache_hit", result.status)
        self.assertEqual(0, provider.calls)
        self.assertEqual("2025-12-31", result.dataset_state.available_through)

    def test_stale_request_falls_back_and_persists_every_layer(self) -> None:
        failing = FakeProvider("primary", priority=10, error=TimeoutError("primary timed out"))
        fallback = FakeProvider("fallback", priority=20)
        kernel = AcquisitionKernel(self.store, [fallback, failing], clock=lambda: self.now)

        result = kernel.acquire(
            self.requirement,
            mode=AcquisitionMode.REFRESH_IF_STALE,
            workflow_run_id="run_test",
        )

        self.assertEqual("acquired", result.status)
        self.assertEqual("fallback", result.provider_id)
        self.assertEqual(1, failing.calls)
        self.assertEqual(1, fallback.calls)
        self.assertEqual(1, result.persisted_documents)
        self.assertEqual(1, result.persisted_facts)
        self.assertEqual(1, result.persisted_evidence_candidates)
        self.assertEqual(["failed", "completed"], [item["status"] for item in self.store.list_runs(result.request_id)])
        self.assertEqual(1, self.store.count("source_document"))
        self.assertEqual(1, self.store.count("normalized_fact"))
        self.assertEqual(1, self.store.count("evidence_candidate"))
        state = self.store.get_dataset_state(self.requirement)
        self.assertEqual("2025-12-31", state.available_through)
        self.assertNotEqual(state.available_through, state.last_checked_at)

    def test_force_refresh_ignores_a_fresh_cache(self) -> None:
        self.store.upsert_dataset_state(
            DatasetState(
                entity_key="300308.SZ",
                data_type="financial_statements",
                market="A",
                available_through="2025-12-31",
                last_checked_at=self.now.isoformat(),
                last_successful_fetch_at=self.now.isoformat(),
                required_fields_present=("net_profit_parent",),
                quality_status="verified",
                is_complete=True,
                source_ids=("cninfo",),
            )
        )
        provider = FakeProvider("cninfo")
        kernel = AcquisitionKernel(self.store, [provider], clock=lambda: self.now)

        result = kernel.acquire(self.requirement, mode=AcquisitionMode.FORCE_REFRESH)

        self.assertEqual("acquired", result.status)
        self.assertEqual(1, provider.calls)

    def test_conflicting_fact_is_quarantined_instead_of_overwriting_verified_fact(self) -> None:
        provider = FakeProvider("cninfo")
        first = AcquisitionKernel(self.store, [provider], clock=lambda: self.now).acquire(
            self.requirement,
            mode=AcquisitionMode.FORCE_REFRESH,
        )
        self.assertEqual("acquired", first.status)
        original = self.store.list_facts("300308.SZ", "financial_statements")[0]

        class ConflictingProvider(FakeProvider):
            def acquire(self, request):
                batch = super().acquire(request)
                return replace(
                    batch,
                    facts=(replace(batch.facts[0], fact_id="fact_conflict", value=200_000_000),),
                )

        conflicting = ConflictingProvider("secondary_official")
        result = AcquisitionKernel(self.store, [conflicting], clock=lambda: self.now).acquire(
            self.requirement,
            mode=AcquisitionMode.FORCE_REFRESH,
        )

        self.assertEqual("acquired_with_conflicts", result.status)
        facts = self.store.list_facts("300308.SZ", "financial_statements")
        self.assertEqual(2, len(facts))
        self.assertEqual("verified", original["verification_status"])
        self.assertEqual("verified", facts[0]["verification_status"])
        self.assertEqual("conflict", facts[1]["verification_status"])
        self.assertEqual("conflict", self.store.get_dataset_state(self.requirement).quality_status)

    def test_provider_payload_below_required_authority_is_rejected_and_falls_back(self) -> None:
        class MislabelledProvider(FakeProvider):
            def acquire(self, request):
                batch = super().acquire(request)
                document = replace(batch.documents[0], authority_tier=AuthorityTier.DISCOVERY)
                return replace(batch, documents=(document,))

        invalid = MislabelledProvider("mislabelled", priority=10)
        official = FakeProvider("official", priority=20)
        result = AcquisitionKernel(self.store, [invalid, official], clock=lambda: self.now).acquire(
            self.requirement,
            mode=AcquisitionMode.FORCE_REFRESH,
        )

        self.assertEqual("acquired", result.status)
        self.assertEqual("official", result.provider_id)
        self.assertEqual("ValueError", result.errors[0]["error_code"])
        self.assertEqual(["failed", "completed"], [item["status"] for item in self.store.list_runs(result.request_id)])


if __name__ == "__main__":
    unittest.main()
