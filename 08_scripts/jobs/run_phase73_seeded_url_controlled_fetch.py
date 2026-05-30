#!/usr/bin/env python3
import argparse,json,sys,urllib.request,urllib.error
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path:sys.path.insert(0,str(L))
from smr_phase73_company_ir_url_seeding import seed_company_ir
from smr_phase73_known_url_seeding import seed_known_urls
def fetch_url(url):
 if not url:return {"http_status":0,"text":"","error":"empty_url"}
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
  with urllib.request.urlopen(req,timeout=20) as resp:
   text=resp.read().decode("utf-8",errors="replace")
  return {"http_status":200,"text":text[:10000],"text_length":len(text)}
 except urllib.error.HTTPError as e:
  return {"http_status":e.code,"text":"","error":str(e)}
 except Exception as e:
  return {"http_status":0,"text":"","error":str(e)[:200]}
def run(mode="execute",tickers=None):
 if tickers is None:tickers=["688041.SH","300394.SZ"]
 urls=[]
 for t in tickers:
  ir=seed_company_ir(t)
  if ir.get("ir_page"):urls.append({"ticker":t,"source_type":"company_ir_page","url":ir["ir_page"]})
  if ir.get("official_site"):urls.append({"ticker":t,"source_type":"company_official_site","url":ir["official_site"]})
  for ku in seed_known_urls(t):
   if ku.get("url"):urls.append({"ticker":t,"source_type":ku["source_type"],"url":ku["url"]})
 rows=[]
 for u in urls:
  if mode=="dry_run":
   rows.append({**u,"http_status":0,"text_length":0,"quality_hint":"dry_run"})
  else:
   fr=fetch_url(u["url"])
   qh="usable" if fr.get("text_length",0)>200 else ("metadata_only" if 0<fr.get("text_length",0)<=200 else "empty")
   rows.append({**u,**fr,"quality_hint":qh,"allowed_usage":"company_context"})
 ok=sum(1 for r in rows if r.get("http_status")==200)
 usable=sum(1 for r in rows if r.get("quality_hint")=="usable")
 return {"phase73_seeded_url_fetch":{"seeded_urls_checked":len(urls),"http_ok":ok,"texts_fetched":ok,"links_found":0,"pdf_links_found":0,"texts_usable":usable,"rows":rows,"raw_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False}}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--dry-run",action="store_true");p.add_argument("--execute",action="store_true")
 p.add_argument("--json",action="store_true")
 a=p.parse_args()
 mode="dry_run" if getattr(a,"dry_run") else "execute"
 r=run(mode)
 print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
