import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
JOBS_DIR = ROOT / "08_scripts" / "jobs"
for path in (LIB_DIR, REPORTING_DIR, JOBS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import apply_watchlist_metadata_patch
from apply_watchlist_metadata_patch import apply_patch_to_payload
from build_phase15_unknown_thesis_diagnostics import simulate_after_patch
from smr_thesis_inference import infer_thesis_type


class Phase16UnknownThesisMetadataTests(unittest.TestCase):
    def test_metadata_patch_simulation_improves_002230_thesis(self):
        patch = {
            "theme_tags": ["ai_infrastructure", "compute_hardware", "server_supply_chain"],
            "business_driver": "AI server / compute infrastructure supply chain",
            "candidate_thesis_hints": ["ai_infrastructure_demand", "revenue_growth"],
            "claim_keywords": ["AI server", "compute", "infrastructure", "revenue growth", "order demand"],
            "proxy_signal_hints": ["order", "guidance", "revenue growth", "industry demand"],
        }
        simulation = simulate_after_patch("002230.SZ", {"theme": "ai_application"}, patch, {})
        self.assertEqual(simulation["candidate_thesis_type"], "ai_infrastructure_demand")
        self.assertGreaterEqual(simulation["simulated_confidence"], 0.5)
        self.assertFalse(simulation["allow_pending"])

    def test_inference_uses_watchlist_metadata_hints(self):
        result = infer_thesis_type(
            "002230.SZ",
            watchlist_item={
                "theme_tags": ["ai_infrastructure"],
                "business_driver": "AI server / compute infrastructure supply chain",
                "candidate_thesis_hints": ["ai_infrastructure_demand"],
            },
        )
        self.assertEqual(result["primary_thesis_type"], "ai_infrastructure_demand")

    def test_patch_only_targets_requested_ticker(self):
        payload = {
            "tickers": [
                {"ticker": "NVDA", "theme": "semiconductor_compute"},
                {"ticker": "002230.SZ", "theme": "ai_application"},
            ]
        }
        patched, changed = apply_patch_to_payload(payload, "002230.SZ", {"theme": "ai_infrastructure", "candidate_thesis_types": ["ai_infrastructure_demand"]})
        self.assertTrue(changed)
        self.assertEqual(patched["tickers"][0]["theme"], "semiconductor_compute")
        self.assertEqual(patched["tickers"][1]["theme"], "ai_infrastructure")
        self.assertNotIn("candidate_thesis_types", patched["tickers"][1])


if __name__ == "__main__":
    unittest.main()
