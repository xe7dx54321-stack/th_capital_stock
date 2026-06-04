import unittest, json, sys, os
sys.path.insert(0,"08_scripts/lib"); sys.path.insert(0,"08_scripts/reporting"); sys.path.insert(0,"08_scripts/jobs")

class TestPhase180WaitingLoop(unittest.TestCase):
    def test_waiting_loop(self):
        from smr_phase180_preview_waiting import build_owner_review_waiting_loop
        w = build_owner_review_waiting_loop()
        wl = w["phase180_owner_review_waiting_loop"]
        self.assertTrue(wl["waiting_loop_active"])
        self.assertEqual(wl["review_input_state"],"no_owner_review_input_pending")
        self.assertEqual(wl["pending_owner_review_count"],9)
        self.assertTrue(wl["no_auto_signoff"])

class TestPhase180Digest(unittest.TestCase):
    def test_owner_action_digest(self):
        from smr_phase180_preview_waiting import build_owner_action_digest
        d = build_owner_action_digest()
        self.assertTrue(d["phase180_owner_action_digest"]["digest_generated"])
        self.assertTrue(len(d["phase180_owner_action_digest"]["actions"])>0)

class TestPhase180Previews(unittest.TestCase):
    def test_daily_preview(self):
        from smr_phase180_preview_waiting import build_daily_brief_packet_preview
        d = build_daily_brief_packet_preview()
        dp = d["phase180_daily_brief_packet_preview"]
        self.assertTrue(dp["preview_gate_generated"])
        self.assertEqual(dp["daily_preview_allowed_count"],0)
        self.assertEqual(dp["blocked_pending_review_count"],9)
        self.assertFalse(dp["auto_publish_daily_brief"])

    def test_weekly_preview(self):
        from smr_phase180_preview_waiting import build_weekly_review_packet_preview
        w = build_weekly_review_packet_preview()
        wp = w["phase180_weekly_review_packet_preview"]
        self.assertTrue(wp["preview_gate_generated"])
        self.assertEqual(wp["weekly_preview_allowed_count"],0)

    def test_brief_safe_summary(self):
        from smr_phase180_preview_waiting import build_brief_safe_summary
        b = build_brief_safe_summary()
        self.assertTrue(b["phase180_brief_safe_summary"]["summary_safe_for_brief"])

class TestPhase180Notification(unittest.TestCase):
    def test_notification_template(self):
        from smr_phase180_preview_waiting import build_notification_template
        n = build_notification_template()
        self.assertTrue(n["phase180_notification_template"]["template_generated"])
        self.assertTrue(n["phase180_notification_template"]["template_not_scheduler_registration"])

class TestPhase180Guards(unittest.TestCase):
    def test_guard(self):
        from smr_phase180_preview_waiting import build_phase180_guard
        g = build_phase180_guard()
        self.assertEqual(g["phase180_guard"]["status"],"pass")
        self.assertFalse(g["phase180_guard"]["auto_publish_disabled"]==False)

    def test_quality_gate(self):
        from smr_phase180_preview_waiting import build_phase180_quality_gate
        q = build_phase180_quality_gate()
        self.assertEqual(q["phase180_quality_gate"]["status"],"pass")

    def test_cc(self):
        from smr_phase180_preview_waiting import build_phase180_cannot_conclude_guard
        c = build_phase180_cannot_conclude_guard()
        self.assertEqual(c["phase180_cannot_conclude_guard"]["status"],"pass")

class TestPhase180Reporting(unittest.TestCase):
    def test_dashboard(self):
        from build_phase180_owner_action_digest import build_dashboard
        d = build_dashboard()
        self.assertEqual(d["phase180_dashboard"]["summary"]["packet_count"],9)

class TestPhase180Pipeline(unittest.TestCase):
    def test_dry_run(self):
        from run_phase180_brief_packet_integration_preview import run_pipeline
        r = run_pipeline("dry-run")
        self.assertEqual(r["phase180_brief_preview_pipeline"]["mode"],"dry-run")
        self.assertEqual(r["phase180_brief_preview_pipeline"]["guard"],"pass")

    def test_execute(self):
        from run_phase180_brief_packet_integration_preview import run_pipeline
        r = run_pipeline("execute")
        self.assertEqual(r["phase180_brief_preview_pipeline"]["packet_count"],9)
        self.assertFalse(r["phase180_brief_preview_pipeline"]["auto_publish_daily_brief"])

    def test_skip_network(self):
        from run_phase180_brief_packet_integration_preview import run_pipeline
        r = run_pipeline("skip-network")
        self.assertEqual(r["phase180_brief_preview_pipeline"]["mode"],"skip-network")

if __name__=="__main__":
    unittest.main()
