def build_feedback_forms():
    forms = {
        "general_feedback": {
            "title": "General Research Feedback",
            "fields": ["date", "observer", "summary", "category", "priority", "tickers_affected", "detail", "suggested_action"],
            "template_md": "# Research Feedback\n\n**Date:** ___\n**Observer:** ___\n**Summary:** ___\n**Category:** [thesis / evidence / source / valuation / gap / other]\n**Priority:** [high / medium / low]\n**Tickers Affected:** ___\n**Detail:** ___\n**Suggested Action:** ___\n",
            "template_json": {"date": "", "observer": "", "summary": "", "category": "", "priority": "", "tickers_affected": [], "detail": "", "suggested_action": ""}
        },
        "source_limitation_confirmation": {
            "title": "Source Limitation Confirmation",
            "fields": ["ticker", "limitation", "current_workaround", "owner_acknowledgment", "upgrade_needed", "notes"],
            "template_md": "# Source Limitation Confirmation\n\n**Ticker:** ___\n**Limitation:** ___\n**Current Workaround:** ___\n**Owner Acknowledgment:** [acknowledged / disputed / needs_investigation]\n**Upgrade Needed:** [yes / no / later]\n**Notes:** ___\n"
        },
        "thesis_review": {
            "title": "Thesis Review Marker",
            "fields": ["ticker", "thesis_statement", "current_status", "owner_assessment", "confidence_change", "new_evidence_since_last_review", "next_review_date"],
            "template_md": "# Thesis Review\n\n**Ticker:** ___\n**Thesis Statement:** ___\n**Current Status:** ___\n**Owner Assessment:** [strengthened / unchanged / weakened / invalidated]\n**Confidence Change:** [up / same / down]\n**New Evidence Since Last Review:** ___\n**Next Review Date:** ___\n"
        },
        "deep_dive_followup": {
            "title": "Deep Dive Follow-up Trigger",
            "fields": ["ticker", "trigger_reason", "scope", "priority", "requested_by", "assigned_to", "deadline"],
            "template_md": "# Deep Dive Follow-up\n\n**Ticker:** ___\n**Trigger Reason:** ___\n**Scope:** ___\n**Priority:** [high / medium / low]\n**Requested By:** ___\n**Assigned To:** ___\n**Deadline:** ___\n"
        },
        "confirmation_checklist": {
            "title": "Ticker Confirmation Checklist",
            "fields": ["ticker", "financial_data_verified", "thesis_status_confirmed", "source_limitations_acknowledged", "gaps_documented", "owner_actions_clear", "ready_for_next_phase"],
            "template_md": "# Confirmation Checklist\n\n**Ticker:** ___\n- [ ] Financial data verified\n- [ ] Thesis status confirmed\n- [ ] Source limitations acknowledged\n- [ ] Gaps documented\n- [ ] Owner actions clear\n- [ ] Ready for next phase\n\n**Owner Signature:** ___\n**Date:** ___\n"
        }
    }
    return {"phase144_feedback_forms": {"forms": len(forms), "form_types": list(forms.keys()), "templates_available": True, "mock_used": False, "fixture_used": False}}
