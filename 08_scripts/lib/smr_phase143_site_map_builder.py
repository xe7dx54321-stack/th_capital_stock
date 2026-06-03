def build_site_map():
    pages = [
        {"id": "home", "title": "Research Console Home", "path": "phase141_research_console.html", "type": "dashboard"},
        {"id": "detail_index", "title": "Ticker Details Index", "path": "phase142_ticker_details/index.html", "type": "index"},
        {"id": "NVDA", "title": "NVDA - NVIDIA Detail", "path": "phase142_ticker_details/NVDA.html", "type": "detail", "market": "US"},
        {"id": "AVGO", "title": "AVGO - Broadcom Detail", "path": "phase142_ticker_details/AVGO.html", "type": "detail", "market": "US"},
        {"id": "688041-SH", "title": "688041.SH - Hygon Detail", "path": "phase142_ticker_details/688041-SH.html", "type": "detail", "market": "CN_A"},
        {"id": "300308-SZ", "title": "300308.SZ - Zhongji Innolight Detail", "path": "phase142_ticker_details/300308-SZ.html", "type": "detail", "market": "CN_A"},
        {"id": "002230-SZ", "title": "002230.SZ - iFLYTEK Detail", "path": "phase142_ticker_details/002230-SZ.html", "type": "detail", "market": "CN_A"},
        {"id": "09988-HK", "title": "09988.HK - Alibaba Detail", "path": "phase142_ticker_details/09988-HK.html", "type": "detail", "market": "HK"},
        {"id": "00700-HK", "title": "00700.HK - Tencent Detail", "path": "phase142_ticker_details/00700-HK.html", "type": "detail", "market": "HK"},
        {"id": "300394-SZ", "title": "300394.SZ - TFC Optical Detail", "path": "phase142_ticker_details/300394-SZ.html", "type": "detail", "market": "CN_A"},
    ]
    return {"phase143_site_map": {"pages": len(pages), "site_map": pages, "mock_used": False, "fixture_used": False}}
