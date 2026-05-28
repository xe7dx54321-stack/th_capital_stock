import unittest

import phase46_helpers  # noqa: F401
from build_phase46_tracking_triggers import build_payload


class Phase46TrackingTriggersTests(unittest.TestCase):
    def test_tracking_triggers_do_not_create_trade_actions(self):
        payload = build_payload("300308.SZ")
        rows = payload["tracking_triggers"]
        trigger_types = {row["trigger_type"] for row in rows}
        self.assertIn("thesis_strengthening_trigger", trigger_types)
        self.assertIn("thesis_weakening_trigger", trigger_types)
        self.assertIn("evidence_update_trigger", trigger_types)
        for row in rows:
            self.assertTrue(row["forbidden_actions"])
            self.assertNotEqual(row["allowed_action"], "create_pending")
            self.assertNotEqual(row["allowed_action"], "create_order")
            self.assertNotEqual(row["allowed_action"], "create_trade")
        self.assertFalse(payload["safety"]["trigger_creates_pending"])
        self.assertFalse(payload["safety"]["trigger_creates_order"])
        self.assertFalse(payload["safety"]["trigger_creates_trade"])


if __name__ == "__main__":
    unittest.main()
