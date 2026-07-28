from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from smr_app.acquisition.contracts import AcquisitionMode, AcquisitionRequest, AuthorityTier, DataRequirement
from smr_app.acquisition.kernel import AcquisitionKernel
from smr_app.acquisition.providers.szse import SzseOfficialProvider
from smr_app.acquisition.store import AcquisitionStore
from smr_app.runtime.migrations import apply_migrations
from tests.acquisition.test_cninfo_provider import ANNUAL_TEXT


class FakeSzseTransport:
    def __init__(self) -> None:
        self.query_calls = []
        self.pdf_calls = []

    def query_announcements(self, payload):
        self.query_calls.append(dict(payload))
        if int(payload.get("pageNum") or 1) == 1:
            return {"announceCount": 31, "data": [{
                "annId": 1226000000, "title": "中际旭创：其他公告",
                "publishTime": "2026-07-01 00:00:00", "attachPath": "/other.PDF",
                "secCode": ["300308"], "secName": ["中际旭创"],
            }]}
        return {"data": [
            {
                "annId": 1225056458, "title": "中际旭创：2025年年度报告摘要",
                "publishTime": "2026-03-31 00:00:00", "attachPath": "/summary.PDF",
                "secCode": ["300308"], "secName": ["中际旭创"],
            },
            {
                "annId": 1225056459, "title": "中际旭创：2025年年度报告",
                "publishTime": "2026-03-31 00:00:00",
                "attachPath": "/disc/disk03/finalpage/2026-03-31/annual.PDF",
                "secCode": ["300308"], "secName": ["中际旭创"],
            },
        ]}

    def fetch_pdf(self, url):
        self.pdf_calls.append(url)
        return b"%PDF-1.7\n" + b"x" * 2048, "application/pdf"


class FailingProvider:
    provider_id = "primary_failure"
    priority = 1
    authority_tier = AuthorityTier.OFFICIAL
    data_types = frozenset({"financial_statements"})
    markets = frozenset({"A"})

    def acquire(self, _request):
        raise TimeoutError("synthetic primary outage")


class SzseProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _request(data_type: str) -> AcquisitionRequest:
        fields = (
            ("announcement_index", "raw_document", "full_text")
            if data_type == "official_filings"
            else ("revenue", "net_profit_parent", "net_profit_excluding_nonrecurring", "operating_cash_flow", "eps", "weighted_roe", "total_assets", "attributable_equity")
        )
        requirement = DataRequirement(
            entity_key="300308.SZ", data_type=data_type, market="A",
            required_fields=fields, minimum_authority=AuthorityTier.OFFICIAL,
        )
        return AcquisitionRequest.create(
            requirement, AcquisitionMode.FORCE_REFRESH, "run-szse-test",
            datetime(2026, 7, 22, tzinfo=timezone.utc),
        )

    def _provider(self) -> SzseOfficialProvider:
        return SzseOfficialProvider(
            cache_root=self.root / "raw", transport=FakeSzseTransport(),
            text_extractor=lambda _: ANNUAL_TEXT + ("年度报告正文。" * 1_000),
            clock=lambda: datetime(2026, 7, 22, tzinfo=timezone.utc),
        )

    def test_szse_shape_selects_full_annual_report_and_builds_eight_latest_facts(self) -> None:
        provider = self._provider()
        batch = provider.acquire(self._request("financial_statements"))
        self.assertEqual("szse_live_index", batch.metadata["index_source"])
        self.assertEqual("2025年年度报告", batch.documents[0].title)
        self.assertTrue(batch.documents[0].source_url.startswith("https://disc.static.szse.cn/download/"))
        self.assertEqual(8, len([item for item in batch.facts if item.as_of == "2025-12-31"]))
        self.assertEqual("300308", provider.transport.query_calls[0]["stock"][0])
        self.assertEqual(2, len(provider.transport.query_calls))

    def test_kernel_uses_szse_after_primary_provider_failure(self) -> None:
        db_path = self.root / "fallback.db"
        apply_migrations(db_path)
        request = self._request("financial_statements")
        result = AcquisitionKernel(
            AcquisitionStore(db_path), (FailingProvider(), self._provider()),
            clock=lambda: datetime(2026, 7, 22, tzinfo=timezone.utc),
        ).acquire(request.requirement, mode=AcquisitionMode.FORCE_REFRESH, workflow_run_id="fallback-test")
        self.assertEqual("acquired", result.status)
        self.assertEqual("szse_official", result.provider_id)
        self.assertEqual("primary_failure", result.errors[0]["provider_id"])


if __name__ == "__main__":
    unittest.main()
