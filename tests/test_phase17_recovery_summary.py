import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
for rel in [("08_scripts", "lib"), ("08_scripts", "reporting"), ("08_scripts", "verification"), ("08_scripts", "jobs")]:
    path = ROOT.joinpath(*rel)
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_phase17_source_chunk_recovery_summary as summary


class Phase17RecoverySummaryTests(unittest.TestCase):
    def test_summary_outputs_sources_chunks_evidence_and_fields(self):
        fake_payload = {
            "generated_at": "now",
            "summary": {
                "targets": ["00700.HK", "300308.SZ"],
                "sources_found": 2,
                "chunks_found": 3,
                "evidence_linked": 3,
                "fields_extracted": 2,
                "fields_derived": 1,
                "remaining_table_not_found": 0,
            },
            "targets": [
                {
                    "ticker": "00700.HK",
                    "source_recovery": {"financial_statement_source_found": True, "balance_sheet_chunk_found": True, "evidence_linked": True, "source_id": "hkex_00700"},
                    "after": {"shareholders_equity": {"status": "extracted"}},
                    "blockers_remaining": [],
                },
                {
                    "ticker": "300308.SZ",
                    "source_recovery": {"financial_statement_source_found": True, "income_statement_chunk_found": True, "evidence_linked": True, "source_id": "cninfo_300308"},
                    "after": {"revenue": {"status": "extracted"}, "gross_profit": {"status": "derived"}},
                    "blockers_remaining": [],
                },
            ],
        }
        with patch.object(summary, "build_payload", return_value=fake_payload):
            payload = summary.compact_summary(summary.build_payload(":memory:", ["00700.HK"], live=False))
        self.assertEqual(payload["summary"]["fields_derived"], 1)
        self.assertEqual(payload["ticker_results"][0]["shareholders_equity_status"], "extracted")
        self.assertIn("Phase 17 Financial Statement Source Chunk Recovery Summary", summary.to_markdown(payload))


if __name__ == "__main__":
    unittest.main()
