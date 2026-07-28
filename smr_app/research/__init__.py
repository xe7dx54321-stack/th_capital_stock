"""Stable research-domain contracts used by governed workflows."""

from .normalization import normalize_research_data
from .stock_packet import build_stock_research_packet

__all__ = ["build_stock_research_packet", "normalize_research_data"]
