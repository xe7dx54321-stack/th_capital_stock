CANDIDATES = ["MRVL","AMAT","LRCX","KLAC","INTC","SNPS","CDNS","CRM","TSM","ASML","AMD","SNOW","MU"]

def build_owner_action_queue_update():
    actions = []
    for tk in CANDIDATES:
        actions.append({
            "ticker": tk,
            "owner_action": "review_candidate_packet_and_submit_decision",
            "owner_action_not_trade": True,
            "no_buy_sell_hold": True,
            "cannot_conclude": ["owner_action_is_not_trade_action", "review_is_not_execution"]
        })
    return {
        "phase167_owner_action_queue_update": {
            "candidates": len(actions),
            "no_buy_sell_hold": True,
            "owner_action_not_trade": True,
            "actions": actions,
            "mock_used": False,
            "fixture_used": False
        }
    }

def build_agent_follow_up_queue_update():
    follow_ups = []
    for tk in CANDIDATES:
        follow_ups.append({
            "ticker": tk,
            "agent_follow_up": "await_owner_decision",
            "agent_follow_up_not_trade": True,
            "no_trade_order_target": True,
            "cannot_conclude": ["agent_follow_up_is_not_trade_instruction", "follow_up_is_not_execution_order"]
        })
    return {
        "phase167_agent_follow_up_queue_update": {
            "candidates": len(follow_ups),
            "no_trade_order_target": True,
            "agent_follow_up_not_trade": True,
            "follow_ups": follow_ups,
            "mock_used": False,
            "fixture_used": False
        }
    }
