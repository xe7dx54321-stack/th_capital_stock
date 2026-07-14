from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class LocalOperationsContractTests(unittest.TestCase):
    def test_doctor_start_and_stop_scripts_have_safe_local_contracts(self) -> None:
        doctor = (ROOT / "scripts" / "doctor.ps1").read_text(encoding="utf-8")
        start = (ROOT / "scripts" / "start-local.ps1").read_text(encoding="utf-8")
        stop = (ROOT / "scripts" / "stop-local.ps1").read_text(encoding="utf-8")
        backup = (ROOT / "scripts" / "backup-local.ps1").read_text(encoding="utf-8")

        self.assertIn('ValidateSet("127.0.0.1")', start)
        self.assertIn("SMR_DB_PATH", start)
        self.assertIn("SMR_API_ORIGIN", start)
        self.assertIn("api\\server.js", start)
        self.assertIn("vite\\bin\\vite.js", start)
        self.assertIn("Test-SmrOwnedProcess", stop)
        self.assertIn("Refusing to stop process", stop)
        self.assertNotIn("taskkill", stop.lower())
        self.assertIn("query_only", (ROOT / "scripts" / "local_db_ops.py").read_text(encoding="utf-8"))
        self.assertNotIn("IFIND_REFRESH_TOKEN=", doctor)
        self.assertIn("local_db_ops.py", backup)
        self.assertIn('"backup"', backup)
        self.assertIn("RetentionDays = 14", backup)
        self.assertIn("StartsWith($rootPrefix", backup)

    def test_vite_proxy_uses_the_runtime_api_origin(self) -> None:
        config = (ROOT / "vite.config.ts").read_text(encoding="utf-8")
        self.assertIn("SMR_API_ORIGIN", config)
        self.assertIn("http://127.0.0.1:3000", config)


if __name__ == "__main__":
    unittest.main()
