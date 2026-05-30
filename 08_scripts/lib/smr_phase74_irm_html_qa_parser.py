#!/usr/bin/env python3
import json,urllib.request,urllib.error,re,hashlib
from pathlib import Path
import sys
L=Path(__file__).resolve().parent
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase74_html_parser_utils import extract_visible_text,extract_links,text_hash,chinese_ratio
IRM_GET_URL="https://irm.cninfo.com.cn/ircs/interaction/getInteraction?stock={code}&pageNum=1&pageSize=20"
def parse_irm_html(ticker:str,skip_network:bool=False):
 code=ticker.split(".")[0];market="SZ" if "SZ" in ticker else "SH"
 if market!="SZ":return{"ticker":ticker,"status":"unsupported_sh","mock_used":False,"fixture_used":False}
 if skip_network:return{"ticker":ticker,"status":"skipped","mock_used":False,"fixture_used":False}
 try:
  req=urllib.request.Request(IRM_GET_URL.format(code=code),headers={"User-Agent":"Mozilla/5.0","Accept":"text/html"})
  with urllib.request.urlopen(req,timeout=20) as resp:
   html=resp.read().decode("utf-8",errors="replace")
  text=extract_visible_text(html)
  links=extract_links(html)
  qa_items=[]
  q_pat=re.compile(r"(?:问|提问|question)[:：]?\s*(.+?)(?:答|回答|answer|回复)",re.DOTALL)
  a_pat=re.compile(r"(?:答|回答|answer|回复)[:：]?\s*(.+?)(?:\n\s*\n|$)",re.DOTALL)
  q_matches=q_pat.findall(text)
  a_matches=a_pat.findall(text)
  for i in range(min(len(q_matches),len(a_matches))):
   q=q_matches[i].strip()[:500];a=a_matches[i].strip()[:2000]
   if q or a:qa_items.append({"question":q,"answer":a,"qa_hash":"sha256:"+hashlib.sha256((q+a).encode()).hexdigest()[:16]})
  usable=sum(1 for qi in qa_items if qi["answer"].strip())
  return{"ticker":ticker,"source_type":"irm_html","html_fetched":True,"qa_items_found":len(qa_items),"qa_text_usable":usable,"qa_items":qa_items,"text_length":len(text),"chinese_ratio":round(chinese_ratio(text),3),"status":"qa_parsed" if qa_items else "qa_structure_not_found","failure_reason":None if qa_items else "html_page_accessible_but_qa_structure_not_found","most_specific_blocker":None if qa_items else "irm_html_requires_client_side_rendering_or_qa_in_table_format","allowed_usage":"management_commentary","raw_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False}
 except Exception as e:
  return{"ticker":ticker,"source_type":"irm_html","html_fetched":False,"qa_items_found":0,"qa_text_usable":0,"status":"parse_failed","failure_reason":str(e)[:200],"most_specific_blocker":"irm_html_fetch_or_parse_failed","raw_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False}
