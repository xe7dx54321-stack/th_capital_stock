import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "verification", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase34_helpers import make_phase34_conn
from validate_phase34_variable_pack_post_governance import build_payload


class Phase34VariablePackPostGovernanceTests(unittest.TestCase):
    def test_downgraded_evidence_lowers_variable_impact_without_confirming(self):
        payload = build_payload(make_phase34_conn(), ticker="300394.SZ")
        row = payload["ticker_results"][0]
        customer = [item for item in row["variable_pack_delta"] if item["variable"] == "customer_allocation_proxy"][0]
        self.assertEqual(customer["delta"], "weakened")
        self.assertFalse(customer["confirmed_after"])
        self.assertEqual(payload["summary"]["confirmed_variables_added"], 0)


if __name__ == "__main__":
    unittest.main()
