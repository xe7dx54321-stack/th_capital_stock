#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
L = Path(__file__).resolve().parents[1] / '08_scripts' / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_real_business_source_text_adapter import (
    check_real_text_availability, get_available_real_source_types,
    get_real_source_inventory, load_business_variable_schema,
    SOURCE_TYPES, REAL_SOURCE_TYPE_MAP,
)

class TestRealBusinessSourceTextAdapter(unittest.TestCase):
    def test_returns_valid_structure(self):
        r = check_real_text_availability('300308.SZ')
        self.assertIn('real_business_source_text_adapter', r)
        d = r['real_business_source_text_adapter']
        self.assertEqual(d['sources_checked'], len(SOURCE_TYPES))
        self.assertFalse(d['mock_sources_used_for_research'])
        self.assertFalse(d['raw_content_saved'])
        self.assertFalse(d['ocr_used'])
        self.assertIn('fixture_used_for_research', d)

    def test_source_rows_complete(self):
        r = check_real_text_availability('300308.SZ')
        rows = r['real_business_source_text_adapter']['source_rows']
        self.assertEqual(len(rows), len(SOURCE_TYPES))
        for row in rows:
            self.assertIn(row['status'], ['real_text_available', 'metadata_only', 'text_unavailable'])

    def test_mock_not_used(self):
        r = check_real_text_availability('300308.SZ')
        self.assertFalse(r['real_business_source_text_adapter']['mock_sources_used_for_research'])

    def test_get_available_types(self):
        types = get_available_real_source_types()
        self.assertIn('investor_relations_record', types)
        self.assertIn('annual_report', types)

    def test_inventory_output(self):
        inv = get_real_source_inventory('300308.SZ')
        self.assertIsInstance(inv, list)
        self.assertGreater(len(inv), 0)
        for item in inv:
            self.assertIn('source_id', item)
            self.assertIn('text_available', item)
            self.assertIn('allowed_usage', item)

    def test_schema_loaded(self):
        schema = load_business_variable_schema()
        self.assertIn('business_variables', schema)
        self.assertGreaterEqual(len(schema['business_variables']), 7)

if __name__ == '__main__': unittest.main()
