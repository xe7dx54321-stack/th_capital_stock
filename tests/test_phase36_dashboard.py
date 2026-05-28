import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase36_evidence_acquisition_dashboard import build_payload, render_markdown
from phase34_helpers import make_phase34_conn


class Phase36EvidenceAcquisitionDashboardTests(unittest.TestCase):
    def test_dashboard_separates_acquisition_and_repair_without_advice(self):
        payload = build_payload(make_phase34_conn())
        summary = payload["summary"]
        self.assertEqual(summary["target_tickers"], ["300308.SZ", "300394.SZ"])
        self.assertEqual(summary["new_pending_created"], 0)
        self.assertEqual(summary["paper_order_created"], 0)
        modes = {row["ticker"]: row["mode"] for row in payload["ticker_rows"]}
        self.assertEqual(modes["300308.SZ"], "targeted_acquisition_plan")
        self.assertEqual(modes["300394.SZ"], "evidence_chain_repair")
        text = render_markdown(payload).lower()
        self.assertNotIn("buy recommendation", text)
        self.assertNotIn("sell recommendation", text)
        self.assertFalse(payload["safety"]["dashboard_is_investment_advice"])


if __name__ == "__main__":
    unittest.main()
