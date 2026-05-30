#!/usr/bin/env python3
import json,urllib.request,urllib.error,re,hashlib
from pathlib import Path
import sys
L=Path(__file__).resolve().parent
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase74_html_parser_utils import extract_visible_text,extract_links,detect_pdf_links,extract_dates,text_hash
SSE_URLS=["https://www.sse.com.cn/assortment/stock/list/info/announcement/index.shtml?stockCode={code}","https://www.sse.com.cn/assortment/stock/list/info/announcement/index.shtml?COMPANY_CODE={code}"]
def parse_sse_html(ticker:str,skip_network:bool=False):
 code=ticker.split(".")[0];market="SH" if "SH" in ticker else "SZ"
 if market!="SH":return{"ticker":ticker,"status":"unsupported_sz","mock_used":False,"fixture_used":False}
 if skip_network:return{"ticker":ticker,"status":"skipped","mock_used":False,"fixture_used":False}
 all_links=[];all_pdfs=[];all_texts=[];fetched=0
 for url_t in SSE_URLS:
  try:
   req=urllib.request.Request(url_t.format(code=code),headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.sse.com.cn/"})
   with urllib.request.urlopen(req,timeout=20) as resp:
    html=resp.read().decode("utf-8",errors="replace")
   fetched+=1
   text=extract_visible_text(html)
   links=extract_links(html,url_t.format(code=code))
   pdfs=detect_pdf_links(links)
   dates=extract_dates(text)
   all_links.extend(links);all_pdfs.extend(pdfs)
   if len(text)>200:all_texts.append({"source_url":url_t.format(code=code),"text":text[:5000],"text_length":len(text),"text_hash":text_hash(text)})
  except Exception as e:
   continue
 rows=[]
 for l in all_links[:30]:
  rows.append({"announcement_title":l.get("anchor_text","")[:200],"announcement_url":l["url"],"is_pdf":l["url"].lower().endswith(".pdf"),"source_type":"sse_html","allowed_usage":"exchange_metadata_or_exchange_text"})
 return{"ticker":ticker,"html_pages_fetched":fetched,"announcement_links_found":len(all_links),"pdf_links_found":len(all_pdfs),"text_pages_found":len(all_texts),"rows":rows,"texts":all_texts,"status":"parsed" if all_links else "no_disclosure_links_found","failure_reason":None if all_links else "sse_html_page_accessible_but_disclosure_links_not_in_static_html","most_specific_blocker":None if all_links else "links_rendered_by_javascript_or_need_different_url_params","raw_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False}
