import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from build_phase21_demand_proxy_gate_summary import compact_payload, render_markdown


class Phase21DemandProxyGateSummaryTests(unittest.TestCase):
    def test_summary_outputs_json_and_markdown_rows(self):
        payload = compact_payload(
            {
                "generated_at": "2026-05-26 10:00:00",
                "summary": {
                    "direct_demand_evidence_added": 2,
                    "proxy_sources_expanded": 1,
                    "bear_case_gate_improved": 1,
                    "new_reduced_size_pending": 0,
                },
                "ticker_results": [
                    {
                        "ticker": "300308.SZ",
                        "after_status": "candidate_shadow",
                        "primary_gate_before": "BEAR_CASE_GATE",
                        "direct_demand_best_strength": "medium_indication",
                        "proxy_sources_after": 2,
                        "proxy_status_after": "medium",
                        "bear_case_status_after": "partially_mitigated",
                        "valuation_status_after": "supporting_evidence",
                        "why_no_pending": ["find confirmed order/customer evidence"],
                        "remaining_warnings": ["confirmed signed order or tender/procurement award"],
                    }
                ],
                "safety": {"promotion_rules_relaxed": False},
            },
            "ai_core",
        )
        markdown = render_markdown(payload)

        self.assertEqual(payload["summary"]["direct_demand_evidence_count"], 2)
        self.assertEqual(payload["rows"][0]["proxy_status"], "medium")
        self.assertIn("Phase 21 Demand / Proxy Gate Summary", markdown)
        self.assertIn("300308.SZ", markdown)


if __name__ == "__main__":
    unittest.main()
