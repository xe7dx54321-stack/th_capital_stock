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

from validate_phase30_post_persistence_audit import build_payload


class Phase30PostPersistenceAuditTests(unittest.TestCase):
    def test_audit_runs_without_confirmed_or_pending(self):
        payload = build_payload(sqlite3.connect(":memory:"), tickers="300394.SZ")
        self.assertEqual(payload["summary"]["confirmed_variables_added"], 0)
        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertFalse(payload["safety"]["confirmed_supplier_share_added"])
        self.assertFalse(payload["safety"]["confirmed_ASP_added"])


if __name__ == "__main__":
    unittest.main()
