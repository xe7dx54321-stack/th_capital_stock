import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestAudit(unittest.TestCase):
    def test_audit(self):from smr_phase82_structured_data_availability_audit import audit_availability;r=audit_availability();a=r["phase82_structured_data_availability_audit"];self.assertGreater(a["tickers_checked"],0)
    def test_not_wrap_unavailable(self):from smr_phase82_structured_data_availability_audit import audit_availability;r=audit_availability();rows=r["phase82_structured_data_availability_audit"]["rows"];self.assertFalse(any(r["structured_data_available"]==False and r["metrics_available"] for r in rows))
    def test_300394_blocked(self):from smr_phase82_structured_data_availability_audit import audit_availability;r=audit_availability();rows=r["phase82_structured_data_availability_audit"]["rows"];row=[x for x in rows if x["ticker"]=="300394.SZ"];self.assertEqual(len(row),1);self.assertFalse(row[0]["structured_data_available"]);self.assertGreater(len(row[0]["most_specific_blocker"]),0)
if __name__=="__main__":unittest.main()
