import unittest
from build_phase49_real_source_monitor_schema import build
from smr_real_source_monitor_schema import SOURCE_TYPES
class Phase49SchemaTests(unittest.TestCase):
    def test_source_types(self): self.assertIn('cninfo_announcement',SOURCE_TYPES); self.assertIn('cninfo_investor_relations',SOURCE_TYPES)
    def test_schema_output(self):
        p=build('300308.SZ'); s=p['event_trigger_schema']
        self.assertGreater(len(s.get('sample_sources')or[]),0)
        self.assertIn('create_pending',s.get('always_forbidden_actions')or[])
    def test_metadata_only(self):
        p=build('300308.SZ')
        for s in p['event_trigger_schema'].get('sample_sources')or[]:
            self.assertTrue(s.get('metadata_only'))
            self.assertFalse(s.get('raw_content_saved'))
if __name__=='__main__': unittest.main()
