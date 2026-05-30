#!/usr/bin/env python3
import argparse,json,sys,urllib.request,urllib.error
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase74_html_parser_utils import extract_visible_text,extract_links,text_hash,chinese_ratio,remove_boilerplate
from smr_phase73_company_ir_url_seeding import seed_company_ir
from smr_phase73_known_url_seeding import seed_known_urls
def fetch_and_extract(url,source_type):
 if not url:return{"url":"","http_status":0,"text_length":0,"text_hash":"","error":"empty_url"}
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"text/html"})
  with urllib.request.urlopen(req,timeout=20) as resp:
   html=resp.read().decode("utf-8",errors="replace")
  text=extract_visible_text(html)
  clean=remove_boilerplate(text)
  links=extract_links(html,url)
  cr=round(chinese_ratio(clean),3)
  qh="usable_company_context" if len(clean)>200 and cr>0.05 else ("text_too_short" if len(clean)<=200 else "low_chinese_ratio")
  return{"url":url,"source_type":source_type,"http_status":200,"text_length":len(clean),"text_hash":text_hash(clean),"chinese_ratio":cr,"links_found":len(links),"quality_hint":qh,"text_preview":clean[:2000],"error":None}
 except Exception as e:
  return{"url":url,"source_type":source_type,"http_status":0,"text_length":0,"error":str(e)[:200]}
def run(mode="execute",tickers=None):
 if tickers is None:tickers=["688041.SH","300394.SZ"]
 urls=[]
 for t in tickers:
  ir=seed_company_ir(t)
  for k in["official_site","ir_page"]:
   if ir.get(k):urls.append((ir[k],f"company_{k}"))
  for ku in seed_known_urls(t):
   if ku.get("url"):urls.append((ku["url"],ku.get("source_type","known_url")))
 rows=[]
 for url,st in urls:
  if mode=="dry_run":rows.append({"url":url,"source_type":st,"http_status":0,"text_length":0,"quality_hint":"dry_run"})
  else:rows.append(fetch_and_extract(url,st))
 ok=sum(1 for r in rows if r.get("http_status")==200)
 usable=sum(1 for r in rows if "usable" in r.get("quality_hint",""))
 return{"phase74_seeded_url_html_text_extract":{"seeded_urls_checked":len(urls),"html_pages_fetched":ok,"texts_extracted":ok,"texts_usable":usable,"rows":rows,"raw_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False}}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true")
 p.add_argument("--json",action="store_true")
 a=p.parse_args()
 mode="dry_run" if getattr(a,"dry_run") else "execute"
 r=run(mode)
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
