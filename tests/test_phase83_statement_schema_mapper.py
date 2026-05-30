import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestSchemaMapper(unittest.TestCase):
    def test_build(self):from smr_phase83_statement_schema_mapper import build_mapping_report;r=build_mapping_report();sm=r["phase83_statement_schema_mapping"];self.assertGreater(sm["metrics_mapped"],0)
    def test_has_revenue(self):from smr_phase83_statement_schema_mapper import build_mapping_report;r=build_mapping_report();rows=r["phase83_statement_schema_mapping"]["rows"];self.assertTrue(any(r["standard_metric"]=="revenue"for r in rows))
    def test_has_derived(self):from smr_phase83_statement_schema_mapper import build_mapping_report;r=build_mapping_report();self.assertGreater(len(r["phase83_statement_schema_mapping"]["derived_metrics"]),0)
if __name__=="__main__":unittest.main()
