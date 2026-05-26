import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, REPORTING_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase25_supply_chain_gap_summary import build_payload, render_markdown
from test_phase25_end_demand_proxy import make_evidence_conn


class Phase25SupplyChainGapSummaryTests(unittest.TestCase):
    def test_summary_outputs_json_and_markdown(self):
        payload = build_payload(make_evidence_conn(), tickers="300394.SZ,300308.SZ")
        markdown = render_markdown(payload)
        self.assertEqual(payload["summary"]["tickers_checked"], 2)
        self.assertIn("300394.SZ", {row["ticker"] for row in payload["rows"]})
        self.assertIn("next_connector_needs", payload)
        self.assertIn("# Phase 25 Supply Chain Expectation Gap Summary", markdown)


if __name__ == "__main__":
    unittest.main()
