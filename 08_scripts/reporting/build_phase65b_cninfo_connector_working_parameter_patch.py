#!/usr/bin/env python3
import argparse,json,sys,urllib.request,urllib.parse
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
CNINFO_API="https://www.cninfo.com.cn/new/hisAnnouncement/query"
HEADERS={"User-Agent":"Mozilla/5.0","Accept":"application/json","Referer":"https://www.cninfo.com.cn/","Content-Type":"application/x-www-form-urlencoded"}
def build(t="300308.SZ",skip=False):
    curated=CURATED_CNINFO_IDENTITIES.get(t,{})
    org_id=curated.get("org_id","")
    code=curated.get("security_code",t.split(".")[0])
    stock_param=code+","+org_id if org_id else code
    plate=curated.get("plate","sz");column=curated.get("column","szse")
    identity_used=bool(org_id)
    r={"ticker":t,"cninfo_connector_working_parameter_patch":{"identity_map_used":identity_used,"stock_param":stock_param,"plate":plate,"column":column,"metadata_sources_found":0,"total_announcement":0,"source_types":{},"raw_content_saved":False,"ocr_used":False,"mock_used":False,"fixture_used":False}}
    p=r["cninfo_connector_working_parameter_patch"]
    if skip:
        p["status"]="skipped_network_disabled";p["failure_reason"]="skip_network"
        return r
    if not identity_used:
        p["status"]="no_identity_found";p["failure_reason"]="no_curated_identity_for_ticker"
        return r
    try:
        params={"pageNum":1,"pageSize":10,"stock":stock_param,"plate":plate,"column":column,"tabName":"fulltext","searchkey":"","secid":"","category":"","trade":"","seDate":""}
        data=urllib.parse.urlencode(params).encode()
        req=urllib.request.Request(CNINFO_API,data=data,headers=dict(HEADERS))
        with urllib.request.urlopen(req,timeout=20) as resp:
            body=json.loads(resp.read().decode("utf-8",errors="replace"))
            p["total_announcement"]=body.get("totalAnnouncement",0)
            anns=body.get("announcements",[])
            p["metadata_sources_found"]=len(anns)
            types={}
            for a in anns:
                ttl=(a.get("announcementTitle","") or "")
                if "年度报告" in ttl: st="annual_report"
                elif "半年度" in ttl: st="semiannual_report"
                elif "季度报告" in ttl or "季报" in ttl: st="quarterly_report"
                elif "投资者关系" in ttl or "调研" in ttl: st="investor_relations_record"
                else: st="announcement"
                types[st]=types.get(st,0)+1
            p["source_types"]=types
        p["status"]="ok" if p["metadata_sources_found"]>0 else "zero_result"
    except Exception as e:
        p["status"]="degraded_network_or_endpoint_failure";p["failure_reason"]=str(e)[:100]
    return r
def _md(r):
    p=r.get("cninfo_connector_working_parameter_patch",r)
    lines=["# CNINFO Connector Working Parameter Patch",""]
    lines.append("Identity Map Used: "+str(p.get("identity_map_used")))
    lines.append("Stock Param: "+str(p.get("stock_param","")))
    lines.append("Metadata Found: "+str(p.get("metadata_sources_found",0)))
    lines.append("Total: "+str(p.get("total_announcement",0)))
    if p.get("source_types"):
        for k,v in p["source_types"].items(): lines.append("- "+k+": "+str(v))
    if p.get("failure_reason"): lines.append("Reason: "+p["failure_reason"])
    return "\n".join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument("--ticker",default="300308.SZ");p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true");p.add_argument("--skip-network",action="store_true")
    a=p.parse_args();r=build(a.ticker,getattr(a,"skip_network",False))
    if a.json: print(json.dumps(r,ensure_ascii=False,indent=2))
    elif a.markdown: print(_md(r))
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
