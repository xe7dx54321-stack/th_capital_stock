from .cninfo import CninfoOfficialProvider, default_cninfo_provider
from .market import (
    CrossValidatedValuationProvider,
    PeerComparisonProvider,
    SzseMarketProvider,
    TencentMarketProvider,
    default_peer_comparison_provider,
    default_szse_market_provider,
    default_tencent_market_provider,
    default_valuation_provider,
)
from .szse import SzseOfficialProvider, default_szse_provider
from .factory import default_research_providers

try:
    # 默认使用本地自托管 Firecrawl；测试必须显式注入 Fake transport。
    from .firecrawl import FirecrawlResearchProvider, default_firecrawl_provider  # noqa: F401
except Exception:  # pragma: no cover - 极端情况下 import 失败也不阻塞主流程
    FirecrawlResearchProvider = None  # type: ignore[assignment,misc]
    default_firecrawl_provider = None  # type: ignore[assignment]


__all__ = [
    "CninfoOfficialProvider", "SzseOfficialProvider", "SzseMarketProvider", "TencentMarketProvider",
    "CrossValidatedValuationProvider", "PeerComparisonProvider",
    "default_cninfo_provider", "default_szse_provider", "default_szse_market_provider",
    "default_tencent_market_provider", "default_valuation_provider", "default_peer_comparison_provider",
    "FirecrawlResearchProvider",
    "default_firecrawl_provider",
    "default_research_providers",
]
