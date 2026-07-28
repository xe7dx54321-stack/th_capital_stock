from __future__ import annotations

from collections.abc import Iterable

from smr_app.acquisition.contracts import AcquisitionProvider

from .cninfo import default_cninfo_provider
from .firecrawl import default_firecrawl_provider
from .market import (
    default_peer_comparison_provider,
    default_szse_market_provider,
    default_tencent_market_provider,
    default_valuation_provider,
)
from .szse import default_szse_provider


def default_research_providers(*, include_open_web: bool = True) -> tuple[AcquisitionProvider, ...]:
    providers: list[AcquisitionProvider] = [
        default_cninfo_provider(),
        default_szse_provider(),
        default_szse_market_provider(),
        default_tencent_market_provider(),
        default_valuation_provider(),
        default_peer_comparison_provider(),
    ]
    if include_open_web:
        providers.append(default_firecrawl_provider())
    return tuple(providers)


def capabilities(providers: Iterable[AcquisitionProvider]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for provider in providers:
        for data_type in sorted(provider.data_types):
            result.setdefault(data_type, []).append(provider.provider_id)
    return result
