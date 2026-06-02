
def build_source_gap_register():
 g=[
  {'id':'09988_hkex_probe','ticker':'09988.HK','severity':'medium','status':'pending_probe'},
  {'id':'00700_hkex_probe','ticker':'00700.HK','severity':'medium','status':'pending_probe'},
  {'id':'NVDA_edgar_probe','ticker':'NVDA','severity':'medium','status':'pending_probe'},
  {'id':'AVGO_edgar_probe','ticker':'AVGO','severity':'medium','status':'pending_probe'},
  {'id':'300394_blocked','ticker':'300394.SZ','severity':'critical','status':'unchanged_manual'},
  {'id':'688041_partial','ticker':'688041.SH','severity':'high','status':'unchanged_owner'},
  {'id':'transcript_manual','ticker':'all_hk_us','severity':'low','status':'manual_required'},
 ]
 return {'phase121_source_gap_register':{'total':len(g),'gaps':g,'mock_used':False,'fixture_used':False}}
