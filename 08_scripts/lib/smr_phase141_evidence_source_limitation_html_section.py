def build_evidence_source_limitation_html_section():
 html='<div class=info-grid>'
 html+='<div class=info-card><h4>Source: 300394.SZ</h4><span class="tag tag-warn">medium</span><p>CNINFO org_id missing. Using eastmoney alternative.</p></div>'
 html+='<div class=info-card><h4>Valuation: 688041.SH</h4><span class="tag tag-warn">medium</span><p>Valuation metrics are derived estimates, not direct market data.</p></div>'
 html+='<div class=info-card><h4>Source: NVDA</h4><span class="tag tag-info">low</span><p>SEC EDGAR direct access limitation. Transcripts manual.</p></div>'
 html+='<div class=info-card><h4>Source: HK tickers</h4><span class="tag tag-info">low</span><p>HKEX official direct limitation.</p></div>'
 html+='</div>'
 return {'phase141_evidence_source_limitation_html_section':{'html':html,'items':4,'not_trade':True,'mock_used':False,'fixture_used':False}}
