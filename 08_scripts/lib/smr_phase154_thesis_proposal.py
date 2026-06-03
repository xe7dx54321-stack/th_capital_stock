def build_thesis_proposal(targets):
    proposals = []
    for t in targets:
        proposals.append({"ticker": t, "thesis_status": "unconfirmed",
                         "proposal": f"Structured research proposal for {t}: to be reviewed by owner.",
                         "cannot_conclude": ["thesis_unconfirmed", "no_customer_or_order_specifics"]})
    return {"phase154_thesis_proposal": {"confirmed_thesis_created": False,
        "proposals": len(proposals), "thesis_proposals": proposals,
        "mock_used": False, "fixture_used": False}}
