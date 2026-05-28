import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase35_variable_coverage_matrix import build_payload, render_markdown
from phase34_helpers import make_phase34_conn


class Phase35VariableMatrixTests(unittest.TestCase):
    def test_matrix_shows_missing_sensitive_variables_without_fabrication(self):
        payload = build_payload(make_phase34_conn(), ticker="300394.SZ")
        rows = {row["variable"]: row for row in payload["variable_matrix"]}
        for variable in ("supplier_share", "ASP_price_proxy", "customer_allocation_proxy", "official_consensus"):
            self.assertIn(variable, rows)
            self.assertFalse(rows[variable]["confirmed"])
        self.assertEqual(rows["official_consensus"]["status"], "missing")
        markdown = render_markdown(payload)
        self.assertIn("official_consensus", markdown)


if __name__ == "__main__":
    unittest.main()
