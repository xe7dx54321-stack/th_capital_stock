def build_ticker_detail_index(ticker_data_list, css_extension):
    cards_html = ''
    for t in ticker_data_list:
        tid = t["ticker"].replace(".", "-")
        mc = {"CN_A":"CN_A","HK":"HK","US":"US"}.get(t["market"],"")
        cc = {"high":"conf-high","medium":"conf-med","low":"conf-low"}.get(t["confidence"],"conf-med")
        cards_html += '<a href="' + tid + '.html" class="ticker-card-link"><div class="ticker-card ' + mc + '"><h3>' + t["ticker"] + ' - ' + t["name"] + '</h3></div></a>'
    ec = '\n.ticker-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;max-width:1200px;margin:0 auto;padding:24px}\n.ticker-card-link{text-decoration:none;color:inherit}\n.ticker-card{background:var(--card-bg);border:1px solid var(--border);border-radius:8px;padding:18px}\n.ticker-card:hover{border-color:var(--accent)}\n.ticker-card.CN_A{border-left:3px solid var(--red)}.ticker-card.HK{border-left:3px solid var(--orange)}.ticker-card.US{border-left:3px solid var(--accent)}\n'
    tpl = '<!DOCTYPE html>\n<html lang=en>\n<head>\n<meta charset=UTF-8>\n<title>TH Capital Research - Ticker Details Index</title>\n<style>__CSS__</style>\n</head>\n<body class=detail-page>\n<header class=detail-header>\n<a href=phase141_research_console.html class=back-link>&larr; Research Console</a>\n<h1>Ticker Detail Pages</h1>\n</header>\n__CARDS__\n<footer class=detail-footer><p>Research-only index. No trade recommendations.</p></footer>\n</body>\n</html>'
    full_css = css_extension + ec
    page = tpl.replace('__CSS__', full_css).replace('__CARDS__', cards_html)
    return page