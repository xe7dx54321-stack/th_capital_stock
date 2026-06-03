def build_decision_cards(ui_model):
    cards = []
    for m in ui_model.get("cards",[]):
        cards.append({"ticker":m["ticker"],"card_html":"<div class='decision-card'><h3>"+m["ticker"]+" - "+m["name"]+"</h3><p>Status: pending_owner_review</p><p>Research activation only. Not investment advice.</p></div>","safety_notes_visible":True,"no_trade_language":True,"no_buy_sell_button":True})
    return {"phase158_decision_cards":{"pending_cards":len(cards),"cards":cards,"static_html_only":True,"mock_used":False,"fixture_used":False}}
