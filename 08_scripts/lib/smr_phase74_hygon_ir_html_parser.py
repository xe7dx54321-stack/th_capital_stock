#!/usr/bin/env python3
import json,urllib.request,urllib.error,re
from pathlib import Path
import sys
L=Path(__file__).resolve().parent
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase74_html_parser_utils import extract_visible_text,extract_links,detect_pdf_links,remove_boilerplate,text_hash,chinese_ratio,is_metadata_only
HYGON_URLS={"official":"https://www.hygon.cn","ir":"https://www.hygon.cn/ir","ir_announcements":"https://www.hygon.cn/ir"}
def parse_hygon_ir(ticker:str="688041.SH",skip_network:bool=False):
 if ticker!="688041.SH":return{"ticker":ticker,"status":"ticker_not_hygon","mock_used":False,"fixture_used":False}
 if skip_network:return{"ticker":ticker,"status":"skipped","mock_used":False,"fixture_used":False}
 results=[];fetched=0
 for page_type,url in HYGON_URLS.items():
  try:
   req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"text/html"})
   with urllib.request.urlopen(req,timeout=20) as resp:
    html=resp.read().decode("utf-8",errors="replace")
   fetched+=1
   text=extract_visible_text(html)
   clean=remove_boilerplate(text)
   links=extract_links(html,url)
   pdfs=detect_pdf_links(links)
   cr=round(chinese_ratio(clean),3)
   meta=is_metadata_only(clean)
   qh="rejected" if meta else ("usable_company_context" if len(clean)>200 and cr>0.1 else ("text_too_short" if len(clean)<=200 else "link_only_page"))
   results.append({"page_type":page_type,"url":url,"text_length":len(clean),"text_hash":text_hash(clean),"chinese_ratio":cr,"is_metadata_only":meta,"announcement_links":len(links),"pdf_links":len(pdfs),"quality_hint":qh,"text_preview":clean[:2000],"allowed_usage":"company_context"})
  except Exception as e:
   results.append({"page_type":page_type,"url":url,"status":"fetch_failed","error":str(e)[:200]})
 texts_usable=sum(1 for r in results if "usable" in r.get("quality_hint",""))
 text_blocks=sum(1 for r in results if r.get("text_length",0)>100)
 return{"ticker":ticker,"pages_checked":len(HYGON_URLS),"pages_fetched":fetched,"text_blocks_found":text_blocks,"announcement_links_found":sum(r.get("announcement_links",0) for r in results),"pdf_links_found":sum(r.get("pdf_links",0) for r in results),"texts_usable":texts_usable,"rows":results,"raw_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False}
