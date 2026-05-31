def run_cn_valuation_adapter():
    results=[]
    for t in['300308.SZ','688041.SH','002230.SZ','300394.SZ']:
        if t=='300394.SZ':results.append({'ticker':t,'market':'CN_A','status':'known_blocked','blocker':'cninfo_org_id_missing','valuation_available':False,'metrics_available':[],'metrics_missing':['market_cap','pe_ttm','ps_ttm','pb'],'source_attempted':[],'source_success':'','data_source':'none'});continue
        code=t.split('.')[0];avail=[];miss=['ev_revenue','ev_ebitda'];va=False;src=''
        try:
            import akshare as ak;df=ak.stock_individual_info_em(symbol=code)
            if df is not None and not df.empty:
                info={row['item']:row['value'] for _,row in df.iterrows() if 'item' in row and 'value' in row};mc=info.get('总市值') or info.get('市值') or info.get('流通市值');pe=info.get('市盈率') or info.get('市盈率-动态');pb=info.get('市净率');ps=info.get('市销率')
                if mc:avail.append('market_cap')
                if pe:avail.append('pe_ttm')
                if pb:avail.append('pb')
                if ps:avail.append('ps_ttm')
                if avail:va=True;src='akshare_stock_individual_info'
        except:pass
        if not va:
            try:
                import yfinance as yf;info=yf.Ticker(t).info or {}
                if info.get('marketCap'):avail.append('market_cap')
                if info.get('trailingPE'):avail.append('pe_ttm')
                if info.get('priceToSalesTrailing12Months'):avail.append('ps_ttm')
                if info.get('priceToBook'):avail.append('pb')
                if avail:va=True;src='yfinance_info'
            except:pass
        if not va:miss=sorted(set(miss+['market_cap','pe_ttm','ps_ttm','pb']))
        results.append({'ticker':t,'market':'CN_A','status':'available' if va else 'unavailable','blocker':'' if va else 'valuation_metrics_unavailable','valuation_available':va,'metrics_available':sorted(set(avail)),'metrics_missing':sorted(set(miss)),'source_attempted':['akshare_stock_individual_info','yfinance_info'],'source_success':src if va else 'none','data_source':'real' if va else 'none'})
    va_count=sum(1 for r in results if r['valuation_available']);pa=sum(1 for r in results if r['valuation_available'] and r['metrics_missing']);kb=sum(1 for r in results if r['status']=='known_blocked')
    return {'phase85_cn_valuation_adapter':{'tickers_checked':len(results),'valuation_available':va_count,'partial':pa,'blocked':kb,'rows':results,'mock_used':False,'fixture_used':False}}
