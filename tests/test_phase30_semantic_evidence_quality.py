import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_semantic_evidence_quality import score_semantic_candidate


def make_candidate(**overrides):
    candidate = {
        "evidence_id": "ev1",
        "ticker": "300308.SZ",
        "source_id": "s1",
        "source_url": "https://static.cninfo.com.cn/a.pdf",
        "source_type": "investor_relations_record",
        "chunk_id": "chunk_0001",
        "quoted_span": "答：公司持续推进高速光模块产能建设，以满足客户需求增长。",
        "variable_type": "capacity_signal",
        "claim_text": "公司推进高速光模块产能建设。",
        "usable_for_promotion": False,
        "payload": {
            "source_metadata": {
                "real_source": True,
                "section_type": "qa_section",
                "published_at": "2026-05-01",
            },
            "gate": {
                "extraction": {
                    "evidence_strength": "management_commentary",
                    "is_company_specific": True,
                    "is_quantified": False,
                    "limitations": ["management commentary"],
                }
            },
        },
    }
    candidate.update(overrides)
    return candidate


class Phase30SemanticEvidenceQualityTests(unittest.TestCase):
    def test_missing_quote_or_url_rejects(self):
        self.assertEqual(score_semantic_candidate(make_candidate(quoted_span=""))["quality_bucket"], "reject")
        self.assertEqual(score_semantic_candidate(make_candidate(source_url=""))["quality_bucket"], "reject")

    def test_management_commentary_capped_below_high_quality(self):
        scored = score_semantic_candidate(make_candidate())
        self.assertIn(scored["quality_bucket"], {"usable", "weak_but_usable"})
        self.assertLess(scored["quality_score"], 85)

    def test_quantified_direct_disclosure_scores_higher(self):
        base = score_semantic_candidate(make_candidate())
        direct = make_candidate(
            quoted_span="公司披露2026年高速光模块相关产能同比提升30%，订单交付按计划推进。",
            payload={
                "source_metadata": {"real_source": True, "section_type": "qa_section", "published_at": "2026-05-01"},
                "gate": {"extraction": {"evidence_strength": "quantified_disclosure", "is_company_specific": True, "is_quantified": True}},
            },
        )
        self.assertGreater(score_semantic_candidate(direct)["quality_score"], base["quality_score"])


if __name__ == "__main__":
    unittest.main()
