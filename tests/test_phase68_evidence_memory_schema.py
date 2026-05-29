import unittest, json, sys, os
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestEvidenceMemorySchema(unittest.TestCase):
    def test_schema_loads(self):
        from smr_evidence_memory_schema import load_schema
        s = load_schema()
        self.assertIn('required_fields', s)
        self.assertIn('evidence_strength_enum', s)
        self.assertGreater(len(s['required_fields']), 5)

    def test_validate_record_ok(self):
        from smr_evidence_memory_schema import validate_record
        ok, missing = validate_record({
            'evidence_id': 'ev_001', 'ticker': '300308.SZ',
            'company_name': 'test', 'industry': 'test', 'phase_source': 'p67b',
            'source_id': 's1', 'source_type': 'annual_report', 'source_title': 'test',
            'business_variable': '800G_product_signal', 'claim_type': 'supported',
            'evidence_strength': 'financial_report_context', 'confidence': 'low',
            'limitation': '', 'cannot_conclude': [], 'allowed_usage': 'brief_support',
            'requires_human_review': False, 'created_at': '2026-01-01'
        })
        self.assertTrue(ok)

    def test_validate_record_missing(self):
        from smr_evidence_memory_schema import validate_record
        ok, missing = validate_record({})
        self.assertFalse(ok)

    def test_strength_enum(self):
        from smr_evidence_memory_schema import validate_strength
        self.assertTrue(validate_strength('financial_report_context'))
        self.assertFalse(validate_strength('invalid'))

    def test_usage_enum(self):
        from smr_evidence_memory_schema import validate_usage
        self.assertTrue(validate_usage('brief_support'))
        self.assertFalse(validate_usage('invalid'))

if __name__ == '__main__': unittest.main()
