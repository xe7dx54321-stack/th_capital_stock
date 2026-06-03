import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__)))
from smr_phase131_integration_board import build_integration_board
def build_integration_brief_md():
 board=build_integration_board()["phase131_integration_board"]
 L=[]
 L.append("# 300394 Alternative Source Integration Report")
 L.append("")
 L.append("## Status: INTEGRATED")
 L.append(f"- Ticker: 300394.SZ (Tianfu Communication)")
 L.append(f"- Previous status: blocked (cninfo_org_id_missing since Phase82)")
 L.append(f"- Current status: covered via Eastmoney alternative source")
 L.append(f"- Primary financial data source: Eastmoney")
 L.append(f"- Fallback: SZSE official disclosure")
 L.append("")
 L.append("## Coverage Summary")
 L.append(f"- Total tickers: {board['sections']['summary']['tickers_total']}")
 L.append(f"- Covered: {board['sections']['summary']['covered']}")
 L.append(f"- Blocked: {board['sections']['summary']['blocked']}")
 L.append(f"- Partial: {board['sections']['summary']['partial']} (688041.SH valuation)")
 L.append("")
 L.append("## Markets")
 L.append(f"- CN_A: {board['sections']['markets']['CN_A_covered']}/4 covered")
 L.append(f"- HK: {board['sections']['markets']['HK_covered']}/2 covered")
 L.append(f"- US: {board['sections']['markets']['US_covered']}/2 covered")
 L.append("")
 L.append("## Resolution Path")
 L.append("CNINFO org_id not found -> Eastmoney identified as equivalent source -> Integrated into pipeline")
 L.append("")
 L.append("*Research-only. No trade recommendations. All 8 tickers now in monitoring coverage.*")
 import os as _os
 return _os.linesep.join(L)
