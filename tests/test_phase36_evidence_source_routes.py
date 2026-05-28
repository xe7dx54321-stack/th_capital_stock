import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase36_evidence_source_routes import build_payload, render_markdown
from phase34_helpers import make_phase34_conn


class Phase36EvidenceSourceRoutesTests(unittest.TestCase):
    def test_routes_do_not_fabricate_sensitive_variables(self):
        payload = build_payload(make_phase34_conn(), ticker="300308.SZ")
        routes_by_variable = {row["variable"]: row["source_routes"] for row in payload["source_routes"]}
        supplier_routes = routes_by_variable["supplier_share"]
        supplier_route_types = {row["route_type"] for row in supplier_routes}
        self.assertIn("manual_research_required", supplier_route_types)
        self.assertIn("not_publicly_confirmable", supplier_route_types)
        self.assertTrue(
            any(row["allowed_usage"] == "none_for_confirmation" for row in supplier_routes),
            "supplier_share must not be planned as confirmed public evidence",
        )
        official_routes = routes_by_variable["official_consensus"]
        self.assertTrue(all("internal proxy" not in row["expected_evidence_type"].lower() for row in official_routes))
        self.assertFalse(payload["safety"]["internal_proxy_treated_as_official_consensus"])
        self.assertFalse(payload["safety"]["supplier_share_public_confirmation_assumed"])
        self.assertIn("Phase 36 Evidence Source Routes", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
