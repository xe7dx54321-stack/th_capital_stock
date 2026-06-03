def build_ticker_card_html_section():
 cards=8
 html='<div class=ticker-grid>'
 html+='<div class="ticker-card US"><h3>NVDA - NVIDIA</h3><div class=meta>US | strengthened | <span class=high>high</span></div><div class=thesis>AI GPU beneficiary</div></div>'
 html+='<div class="ticker-card US"><h3>AVGO - Broadcom</h3><div class=meta>US | supported | <span class=medium>medium</span></div><div class=thesis>AI networking</div></div>'
 html+='<div class="ticker-card CN_A"><h3>688041.SH - Hygon</h3><div class=meta>CN_A | supported | <span class=medium>medium</span></div><div class=thesis>Semiconductor substitution</div><div class=meta>Note: valuation derived</div></div>'
 html+='<div class="ticker-card HK"><h3>09988.HK - Alibaba</h3><div class=meta>HK | observed | <span class=medium>medium</span></div><div class=thesis>Cloud acceleration</div></div>'
 html+='<div class="ticker-card HK"><h3>00700.HK - Tencent</h3><div class=meta>HK | observed | <span class=medium>medium</span></div><div class=thesis>Gaming/ad recovery</div></div>'
 html+='<div class="ticker-card CN_A"><h3>300308.SZ - Zhongji Innolight</h3><div class=meta>CN_A | context_supported | <span class=medium>medium</span></div><div class=thesis>Optical demand</div></div>'
 html+='<div class="ticker-card CN_A"><h3>002230.SZ - iFLYTEK</h3><div class=meta>CN_A | context_supported | <span class=medium>medium</span></div><div class=thesis>AI/software stable</div></div>'
 html+='<div class="ticker-card CN_A"><h3>300394.SZ - TFC Optical</h3><div class=meta>CN_A | unconfirmed | <span class=low>low</span></div><div class=thesis>Optical devices</div><div class=meta>Note: cninfo missing</div></div>'
 html+='</div>'
 return {'phase141_ticker_card_html_section':{'html':html,'cards':cards,'not_trade':True,'mock_used':False,'fixture_used':False}}
