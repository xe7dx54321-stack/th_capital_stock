from __future__ import annotations

import unittest
from datetime import datetime, timezone

from smr_app.acquisition.contracts import AcquisitionMode, AuthorityTier
from smr_app.research.data_requirements_v3 import (
    build_stock_data_requirement_manifest,
    requirement_from_manifest_item,
)
from smr_app.research.research_plan_v3 import build_stock_research_plan


class StockDataRequirementManifestTests(unittest.TestCase):
    def test_manifest_covers_each_required_research_dataset(self) -> None:
        plan = build_stock_research_plan("300308.SZ", "A")

        manifest = build_stock_data_requirement_manifest(
            "300308.SZ",
            "A",
            plan,
            generated_at=datetime(2026, 7, 22, 3, 0, tzinfo=timezone.utc),
        )

        self.assertEqual("1.0", manifest["manifest_version"])
        self.assertEqual("300308.SZ", manifest["entity_key"])
        by_type = {item["data_type"]: item for item in manifest["requirements"]}
        self.assertEqual(
            {
                "official_filings",
                "financial_statements",
                "daily_bars",
                "realtime_quote",
                "valuation_snapshot",
                "peer_comparison",
                "news_research",
            },
            set(by_type),
        )
        self.assertTrue(
            {
                "revenue",
                "net_profit_parent",
                "net_profit_excluding_nonrecurring",
                "operating_cash_flow",
                "eps",
                "weighted_roe",
                "total_assets",
                "attributable_equity",
            }.issubset(by_type["financial_statements"]["required_fields"])
        )
        self.assertEqual("official", by_type["financial_statements"]["minimum_authority"])
        self.assertEqual("reputable_secondary", by_type["realtime_quote"]["minimum_authority"])
        self.assertEqual(
            {"raw_document", "source_url", "evidence_candidates"},
            set(by_type["news_research"]["required_fields"]),
        )
        self.assertIn("300308.SZ", by_type["news_research"]["acquisition_metadata"]["search_query"])

    def test_manifest_item_round_trips_to_kernel_requirement(self) -> None:
        manifest = build_stock_data_requirement_manifest(
            "300308.SZ",
            "A",
            build_stock_research_plan("300308.SZ", "A"),
        )
        item = next(row for row in manifest["requirements"] if row["data_type"] == "financial_statements")

        requirement = requirement_from_manifest_item(item)

        self.assertEqual("300308.SZ", requirement.entity_key)
        self.assertEqual(AuthorityTier.OFFICIAL, requirement.minimum_authority)
        self.assertGreater(requirement.maximum_age.total_seconds(), 0)

    def test_acquisition_modes_are_stable_public_values(self) -> None:
        self.assertEqual(
            ["cache_only", "refresh_if_stale", "force_refresh"],
            [item.value for item in AcquisitionMode],
        )


if __name__ == "__main__":
    unittest.main()
