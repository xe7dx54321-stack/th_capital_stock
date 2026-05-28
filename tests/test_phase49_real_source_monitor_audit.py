import unittest
from phase49_helpers import make_phase49_active_conn
from build_phase49_real_source_monitor_audit import build
class Phase49AuditTests(unittest.TestCase):
    def test_audit_records(self):
        conn=make_phase49_active_conn(); p=build(conn,'300308.SZ')
        self.assertGreaterEqual(p['audit_records'],1)
    def test_no_pending_order_trade(self):
        conn=make_phase49_active_conn(); p=build(conn,'300308.SZ')
        for r in p['audit_rows']:
            self.assertFalse(r['pending_created']); self.assertFalse(r['paper_order_created']); self.assertFalse(r['real_trade_created'])
if __name__=='__main__': unittest.main()
