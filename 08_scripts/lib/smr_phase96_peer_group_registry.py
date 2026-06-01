import json,os
def build_peer_group_registry():
    from smr_phase96_config import get_peer_groups
    pg=get_peer_groups()
    rows=[]
    for gname,tickers in pg.items():
        for t in tickers: rows.append({"ticker":t,"peer_group":gname,"peer_tickers":[x for x in tickers if x!=t]})
    return {"phase96_peer_group_registry":{"peer_groups_created":len(pg),"peer_groups":list(pg.keys()),"ticker_mappings":rows,"mock_used":False,"fixture_used":False}}
