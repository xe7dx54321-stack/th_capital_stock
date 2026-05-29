#!/usr/bin/env python3
import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parent.parent / "08_scripts" / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestPhase64ConnectorHealthDashboard(unittest.TestCase):
    def test_output_has_summary(self):
        from smr_disclosure_source_fallback_router import route_disclosure_source
        r = route_disclosure_source("300308.SZ", skip_network=True)
        router = r["disclosure_source_fallback_router"]
        self.assertIn("cninfo_status", router)
        self.assertIn("szse_status", router)
        self.assertIn("irm_status", router)

    def test_skip_network_ok(self):
        import sys, json
        sys.argv = ["test", "--ticker", "300308.SZ", "--json", "--skip-network"]
        # just make sure the module imports
        from smr_disclosure_source_fallback_router import route_disclosure_source
        result = route_disclosure_source("300308.SZ", skip_network=True)
        self.assertIn("disclosure_source_fallback_router", result)

    def test_degraded_when_no_sources(self):
        from smr_disclosure_source_fallback_router import route_disclosure_source
        r = route_disclosure_source("300308.SZ", skip_network=True)
        router = r["disclosure_source_fallback_router"]
        self.assertFalse(router["real_metadata_available"])
        self.assertFalse(router["real_text_available"])

if __name__ == "__main__": unittest.main()
