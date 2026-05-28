import unittest

from build_phase47_tracking_variable_snapshot import build_payload


class Phase47TrackingVariableSnapshotTests(unittest.TestCase):
    def test_snapshot_covers_11_variables(self):
        payload = build_payload("300308.SZ")
        snap = payload["tracking_variable_snapshot"]
        self.assertEqual(snap["variables_checked"], 11)
        self.assertEqual(len(snap["snapshot_rows"]), 11)

    def test_snapshot_delta_classifications(self):
        payload = build_payload("300308.SZ")
        rows = payload["tracking_variable_snapshot"]["snapshot_rows"]
        deltas = {r["delta"] for r in rows}
        self.assertTrue(deltas.issubset({
            "strengthened", "weakened", "unchanged_positive",
            "unchanged_gap", "needs_more_evidence",
        }))

    def test_summary_counts(self):
        payload = build_payload("300308.SZ")
        summary = payload["tracking_variable_snapshot"]["summary"]
        total = sum(summary.values())
        self.assertEqual(total, 11)

    def test_safety_gates(self):
        payload = build_payload("300308.SZ")
        safety = payload["safety"]
        self.assertFalse(safety["snapshot_is_trading_signal"])
        self.assertFalse(safety["snapshot_triggers_pending"])
        self.assertEqual(safety["pending_created"], 0)
        self.assertEqual(safety["paper_order_created"], 0)

    def test_markdown_output(self):
        from build_phase47_tracking_variable_snapshot import render_markdown
        payload = build_payload("300308.SZ")
        md = render_markdown(payload)
        self.assertIn("Tracking Variable Snapshot", md)
        self.assertIn("300308.SZ", md)


if __name__ == "__main__":
    unittest.main()
