#!/usr/bin/env python3
import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parent.parent / "08_scripts" / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestPhase64FallbackRouter(unittest.TestCase):
    def test_skip_network_all_unreachable(self):
        from smr_disclosure_source_fallback_router import route_disclosure_source
        r = route_disclosure_source("300308.SZ", skip_network=True)
        router = r["disclosure_source_fallback_router"]
        self.assertEqual(router["cninfo_status"], "unreachable")
        self.assertEqual(router["szse_status"], "unreachable")
        self.assertEqual(router["irm_status"], "unreachable")
        self.assertFalse(router["real_metadata_available"])
        self.assertFalse(router["real_text_available"])

    def test_no_mock_no_fixture(self):
        from smr_disclosure_source_fallback_router import route_disclosure_source
        r = route_disclosure_source("300308.SZ", skip_network=True)
        router = r["disclosure_source_fallback_router"]
        self.assertFalse(router["mock_used"])
        self.assertFalse(router["fixture_used"])

    def test_has_routing_reasons(self):
        from smr_disclosure_source_fallback_router import route_disclosure_source
        r = route_disclosure_source("300308.SZ", skip_network=True)
        router = r["disclosure_source_fallback_router"]
        self.assertIsInstance(router["routing_reason"], list)
        self.assertGreater(len(router["routing_reason"]), 0)

    def test_fallback_order_present(self):
        from smr_disclosure_source_fallback_router import route_disclosure_source
        r = route_disclosure_source("300308.SZ", skip_network=True)
        router = r["disclosure_source_fallback_router"]
        self.assertIn("fallback_order", router)

    def test_company_site_not_configured(self):
        from smr_disclosure_source_fallback_router import route_disclosure_source
        r = route_disclosure_source("300308.SZ", skip_network=True)
        router = r["disclosure_source_fallback_router"]
        self.assertEqual(router["company_site_status"], "not_configured")

if __name__ == "__main__": unittest.main()
