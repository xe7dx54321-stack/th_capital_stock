#!/usr/bin/env python3
"""Tests for Phase 64 CNINFO endpoint diagnostics."""

import json
import unittest
import sys
from pathlib import Path

L = Path(__file__).resolve().parent.parent / "08_scripts" / "lib"
if str(L) not in sys.path:
    sys.path.insert(0, str(L))


class TestPhase64CNINFOEndpointDiagnostics(unittest.TestCase):

    def test_skip_network_produces_valid_result(self):
        from smr_cninfo_endpoint_diagnostics import run_cninfo_diagnostics
        result = run_cninfo_diagnostics("300308.SZ", skip_network=True)
        self.assertEqual(result["ticker"], "300308.SZ")
        d = result["cninfo_endpoint_diagnostics"]
        self.assertFalse(d["network_attempted"])
        self.assertEqual(d["status"], "skipped_network_disabled")

    def test_output_has_required_fields(self):
        from smr_cninfo_endpoint_diagnostics import run_cninfo_diagnostics
        result = run_cninfo_diagnostics("300308.SZ", skip_network=True)
        d = result["cninfo_endpoint_diagnostics"]
        for field in ["network_attempted", "dns_ok", "https_connect_ok", "likely_root_cause", "recommended_next_action"]:
            self.assertIn(field, d)

    def test_dns_test_function(self):
        from smr_cninfo_endpoint_diagnostics import _test_dns
        dns_result = _test_dns("www.cninfo.com.cn", timeout=5)
        self.assertIn("dns_ok", dns_result)

    def test_announcement_query_skip_network(self):
        from smr_cninfo_endpoint_diagnostics import run_cninfo_diagnostics
        result = run_cninfo_diagnostics("300308.SZ", skip_network=True)
        d = result["cninfo_endpoint_diagnostics"]
        self.assertEqual(d["dns_ok"], False)
        self.assertEqual(d["likely_root_cause"], "skip_network_enabled")


if __name__ == "__main__":
    unittest.main()
