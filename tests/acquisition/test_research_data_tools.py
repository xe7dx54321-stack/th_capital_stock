from __future__ import annotations

import tempfile
import os
from pathlib import Path

import pytest
from smr_app.acquisition.contracts import AcquisitionMode
from smr_app.acquisition.providers.firecrawl import FakeFirecrawlTransport, FirecrawlResearchProvider
from smr_app.research.data_requirements_v3 import build_stock_data_requirement_manifest
from smr_app.research.research_plan_v3 import build_stock_research_plan
from smr_app.tools.research_data import ResearchDataTools


def test_shared_research_data_tools_acquires_open_web_with_explicit_test_transport() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        fake = FakeFirecrawlTransport()
        provider = FirecrawlResearchProvider(
            transport=fake,
            cache_root=root / "cache",
        )
        tools = ResearchDataTools(root / "runtime.db", providers=(provider,))
        manifest = build_stock_data_requirement_manifest(
            "300308.SZ",
            "A",
            build_stock_research_plan("300308.SZ", "A"),
        )

        status = tools.provider_status()
        assert status["capabilities"]["news_research"] == ["firecrawl_research"]
        assert status["providers"][0]["mode"] == "explicit"

        result = tools.acquire_manifest(
            manifest,
            mode=AcquisitionMode.FORCE_REFRESH,
            only_data_types={"news_research"},
            workflow_run_id="run_shared_tools",
        )
        acquired = result["results"]["300308.SZ:news_research"]
        assert acquired["status"] in {"acquired", "partial"}
        assert acquired["provider_id"] == "firecrawl_research"
        assert acquired["persisted_documents"] >= 1
        assert acquired["persisted_evidence_candidates"] >= 1
        # 已配置公司官方研究入口时直接抓一手来源，不把搜索服务当作单点依赖。
        assert len(fake.search_calls) == 0
        assert fake.scrape_calls[0]["url"] == "https://www.zj-innolight.com/cn"


@pytest.mark.skipif(os.environ.get("SMR_LIVE_TESTS") != "1", reason="requires local Firecrawl")
def test_default_status_probes_real_local_firecrawl() -> None:
    with tempfile.TemporaryDirectory() as temp:
        status = ResearchDataTools(Path(temp) / "runtime.db").provider_status(
            probe_local_firecrawl=True
        )
        firecrawl = next(
            item for item in status["providers"] if item["provider_id"] == "firecrawl_research"
        )
        assert firecrawl["mode"] == "local_http"
        assert firecrawl["base_url"].startswith("http://127.0.0.1:")
        assert firecrawl["reachable"] is True
