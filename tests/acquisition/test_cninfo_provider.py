from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from smr_app.acquisition.contracts import AcquisitionMode, AcquisitionRequest, AuthorityTier, DataRequirement
from smr_app.acquisition.providers.cninfo import CninfoOfficialProvider
from smr_app.acquisition.store import AcquisitionStore
from smr_app.research.acquisition_materializer_v3 import materialize_acquired_stock_data
from smr_app.runtime.migrations import apply_migrations


ANNUAL_TEXT = """主要会计数据和财务指标
2025 年
2024 年
本年比上年增减
2023 年
38,239,935,640.67
23,862,159,738.37
60.25%
10,717,984,471.03
10,797,254,300.45
5,171,485,967.85
108.78%
2,173,527,747.77
10,710,053,246.51
5,068,356,338.29
111.31%
2,123,669,234.59
10,896,126,160.03
3,164,582,957.85
244.31%
1,897,126,918.71
9.80
9.71
4.72
4.63
107.63%
109.72%
2.00
1.97
43.84%
31.23%
12.61%
16.58%
45,288,970,887.78
28,866,276,555.26
56.89%
20,006,747,461.32
29,765,156,275.68
19,133,887,012.66
55.56%
14,261,022,312.40
公司最近三个会计年度不存在持续经营不确定性。
公司主要业务为高端光通信收发模块的研发、生产及销售。
风险因素包括行业需求波动和客户集中度。
"""


class FakeTransport:
    def __init__(self, *, query_fails: bool = False) -> None:
        self.query_fails = query_fails
        self.query_calls = []
        self.pdf_calls = []

    def query_announcements(self, form):
        self.query_calls.append(dict(form))
        if self.query_fails:
            raise TimeoutError("synthetic timeout")
        return {
            "announcements": [
                {
                    "announcementId": "summary",
                    "secCode": "300308",
                    "secName": "中际旭创",
                    "announcementTitle": "2025年年度报告摘要",
                    "announcementTime": 1774886400000,
                    "adjunctUrl": "summary.PDF",
                },
                {
                    "announcementId": "1225056459",
                    "secCode": "300308",
                    "secName": "中际旭创",
                    "announcementTitle": "2025年年度报告",
                    "announcementTime": 1774886400000,
                    "adjunctUrl": "finalpage/2026-03-31/1225056459.PDF",
                },
            ]
        }

    def fetch_pdf(self, url):
        self.pdf_calls.append(url)
        return b"%PDF-1.7\n" + b"x" * 2048, "application/pdf"


class CninfoProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.identity_path = self.root / "identities.json"
        self.identity_path.write_text(json.dumps({
            "identities": {
                "300308.SZ": {
                    "security_code": "300308", "security_name": "中际旭创",
                    "org_id": "9900022016", "plate": "sz", "column": "szse",
                    "known_annual_report": {
                        "announcement_id": "1225056459", "security_code": "300308",
                        "security_name": "中际旭创", "title": "2025年年度报告",
                        "published_at": "2026-03-31",
                        "adjunct_url": "finalpage/2026-03-31/1225056459.PDF",
                    },
                }
            }
        }, ensure_ascii=False), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _request(self, data_type: str) -> AcquisitionRequest:
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
            requirement, AcquisitionMode.FORCE_REFRESH, "run-test",
            datetime(2026, 7, 22, tzinfo=timezone.utc),
        )

    def _provider(self, transport: FakeTransport) -> CninfoOfficialProvider:
        return CninfoOfficialProvider(
            cache_root=self.root / "raw", identity_path=self.identity_path,
            transport=transport, text_extractor=lambda _: ANNUAL_TEXT + ("年度报告正文。" * 1_000),
            clock=lambda: datetime(2026, 7, 22, tzinfo=timezone.utc),
        )

    def test_official_filing_uses_exact_identity_and_persists_validated_raw_pdf(self) -> None:
        transport = FakeTransport()
        batch = self._provider(transport).acquire(self._request("official_filings"))
        self.assertTrue(batch.is_complete)
        self.assertEqual(("announcement_index", "raw_document", "full_text"), batch.required_fields_present)
        self.assertEqual("300308,9900022016", transport.query_calls[0]["stock"])
        self.assertEqual("category_ndbg_szsh", transport.query_calls[0]["category"])
        document = batch.documents[0]
        self.assertEqual("2025年年度报告", document.title)
        self.assertEqual("2026-03-31", document.published_at)
        self.assertTrue(Path(document.metadata["raw_file_path"]).exists())
        self.assertEqual(64, len(document.metadata["raw_sha256"]))

    def test_financial_statement_builds_three_year_facts_and_eight_latest_fields(self) -> None:
        batch = self._provider(FakeTransport()).acquire(self._request("financial_statements"))
        latest = [item for item in batch.facts if item.as_of == "2025-12-31"]
        self.assertEqual(8, len(latest))
        self.assertEqual(set(self._request("financial_statements").requirement.required_fields), set(batch.required_fields_present))
        values = {item.field_name: item.value for item in latest}
        self.assertAlmostEqual(38_239_935_640.67, values["revenue"])
        self.assertAlmostEqual(10_797_254_300.45, values["net_profit_parent"])
        self.assertAlmostEqual(10_896_126_160.03, values["operating_cash_flow"])
        self.assertAlmostEqual(0.4384, values["weighted_roe"])
        self.assertEqual(8, len(batch.evidence_candidates))

    def test_verified_manifest_is_used_only_when_live_index_fails(self) -> None:
        batch = self._provider(FakeTransport(query_fails=True)).acquire(self._request("official_filings"))
        self.assertEqual("verified_manifest_fallback", batch.metadata["index_source"])

    def test_newer_verified_manifest_supersedes_a_stale_live_index(self) -> None:
        transport = FakeTransport()
        original_query = transport.query_announcements

        def stale_query(form):
            payload = original_query(form)
            payload["announcements"][1].update({
                "announcementId": "1223000000",
                "announcementTitle": "2024年年度报告",
                "announcementTime": 1745539200000,
                "adjunctUrl": "finalpage/2025-04-25/1223000000.PDF",
            })
            return payload

        transport.query_announcements = stale_query
        batch = self._provider(transport).acquire(self._request("official_filings"))
        self.assertEqual("verified_manifest_preferred", batch.metadata["index_source"])
        self.assertEqual("2025年年度报告", batch.documents[0].title)

    def test_materializer_promotes_verified_facts_and_official_evidence_into_v3_context(self) -> None:
        db_path = self.root / "control.db"
        apply_migrations(db_path)
        store = AcquisitionStore(db_path)
        provider = self._provider(FakeTransport())
        for data_type in ("official_filings", "financial_statements"):
            request = self._request(data_type)
            store.create_request(request)
            store.persist_batch(request, provider.provider_id, provider.acquire(request), "2026-07-22T00:00:00+00:00")
        fundamentals = {"revenue": 1.0, "period": "1900"}
        valuation = {}
        evidence = {"items": []}
        freshness = {}
        context = {
            "provider_status": {}, "corpus": {"filings": [], "chunks": []},
            "instruments": {"target": {}},
        }
        result = materialize_acquired_stock_data(
            store, ticker="300308.SZ", fundamentals=fundamentals,
            valuation=valuation, evidence=evidence, research_context=context, freshness=freshness,
        )
        self.assertTrue(result["financial_snapshot_materialized"])
        self.assertAlmostEqual(38_239_935_640.67, fundamentals["revenue"])
        self.assertAlmostEqual(10_797_254_300.45, fundamentals["net_income"])
        self.assertEqual("2025", fundamentals["period"])
        self.assertGreaterEqual(len(evidence["items"]), 8)
        self.assertTrue(all(item["source_type"] == "annual_report" for item in evidence["items"]))
        self.assertTrue(context["corpus"]["filings"])
        self.assertTrue(any("主要会计数据" in item["text"] for item in context["corpus"]["chunks"]))


if __name__ == "__main__":
    unittest.main()
