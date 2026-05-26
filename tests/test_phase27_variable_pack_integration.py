import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
for path in (LIB_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from validate_phase27_semantic_variable_pack_integration import build_payload


class Phase27VariablePackIntegrationTests(unittest.TestCase):
    def test_semantic_evidence_updates_packs_without_confirmed_variables(self):
        payload = build_payload(sqlite3.connect(":memory:"), tickers="300394.SZ", mode="mock")
        self.assertEqual(payload["summary"]["tickers_checked"], 1)
        self.assertGreater(payload["summary"]["variable_packs_updated"], 0)
        self.assertEqual(payload["summary"]["confirmed_variables_added"], 0)
        self.assertFalse(payload["safety"]["semantic_evidence_direct_promotion"])


if __name__ == "__main__":
    unittest.main()
