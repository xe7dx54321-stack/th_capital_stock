#!/usr/bin/env python3
"""Tests for Phase 64 disclosure source endpoint registry."""

import json
import unittest
import sys
from pathlib import Path

L = Path(__file__).resolve().parent.parent / "08_scripts" / "lib"
if str(L) not in sys.path:
    sys.path.insert(0, str(L))


class TestPhase64DisclosureEndpointRegistry(unittest.TestCase):

    def test_registry_loads(self):
        from smr_a_share_disclosure_endpoint_registry import load_endpoint_registry
        registry = load_endpoint_registry()
        self.assertIn("sources", registry)
        self.assertIsInstance(registry["sources"], list)

    def test_registry_has_cninfo_szse_irm(self):
        from smr_a_share_disclosure_endpoint_registry import load_endpoint_registry
        registry = load_endpoint_registry()
        platforms = set(s.get("platform") for s in registry["sources"])
        for p in ["cninfo", "szse", "irm"]:
            self.assertIn(p, platforms, f"{p} should be in registry")

    def test_registry_no_raw_no_ocr(self):
        from smr_a_share_disclosure_endpoint_registry import load_endpoint_registry
        registry = load_endpoint_registry()
        for src in registry["sources"]:
            self.assertFalse(src.get("raw_content_saved", True), f"{src['source_id']}: raw_content_saved should be false")
            self.assertFalse(src.get("ocr_allowed", True), f"{src['source_id']}: ocr_allowed should be false")

    def test_get_source_by_id(self):
        from smr_a_share_disclosure_endpoint_registry import get_source_by_id
        src = get_source_by_id("cninfo_his_announcement_query")
        self.assertIsNotNone(src)
        self.assertEqual(src["platform"], "cninfo")

    def test_get_sources_by_platform(self):
        from smr_a_share_disclosure_endpoint_registry import get_sources_by_platform
        sources = get_sources_by_platform("cninfo")
        self.assertGreater(len(sources), 0)

    def test_fallback_order(self):
        from smr_a_share_disclosure_endpoint_registry import get_fallback_order
        order = get_fallback_order()
        self.assertGreater(len(order), 0)
        priorities = [s["fallback_priority"] for s in order]
        self.assertEqual(priorities, sorted(priorities))

    def test_endpoint_summary(self):
        from smr_a_share_disclosure_endpoint_registry import get_endpoint_summary
        summary = get_endpoint_summary()
        self.assertIn("total_sources", summary)
        self.assertGreater(summary["total_sources"], 0)
        self.assertTrue(summary["raw_content_saved_all"])
        self.assertTrue(summary["ocr_allowed_all"])


if __name__ == "__main__":
    unittest.main()
