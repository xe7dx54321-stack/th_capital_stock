#!/usr/bin/env python3
"""SZSE endpoint explorer - Phase 65."""
from __future__ import annotations
import json, urllib.request, urllib.error
from typing import Any

SZSE_ENDPOINTS = [
    {"url":"https://www.szse.cn/api/disc/announcement/annList","method":"GET","desc":"annList GET"},
    {"url":"https://www.szse.cn/api/disc/announcement/annList","method":"POST","desc":"annList POST"},
    {"url":"https://www.szse.cn/disclosure/listed/notice/index.html","method":"GET","desc":"disclosure page"},
    {"url":"https://www.szse.cn/api/disc/announcement/queryAnnList","method":"GET","desc":"queryAnnList GET"},
    {"url":"https://www.szse.cn/api/disc/announcement/queryAnnList","method":"POST","desc":"queryAnnList POST"},
]
HEADERS = {"User-Agent":"Mozilla/5.0","Accept":"application/json, text/html","Accept-Language":"zh-CN"}

def explore_szse_endpoints(ticker="300308.SZ",skip_network=False):
    code=ticker.split(".")[0] if "." in ticker else ticker
    r={"ticker":ticker,"szse_endpoint_explorer":{"network_attempted":not skip_network,"endpoints_tested":0,"working_endpoints":[],"failed_endpoints":[],"best_endpoint":None,"mock_used":False,"fixture_used":False}}
    e=r["szse_endpoint_explorer"]
    if skip_network: e["status"]="skipped";return r
    for ep in SZSE_ENDPOINTS:
        e["endpoints_tested"]+=1
        trial={"endpoint":ep["url"],"method":ep["method"],"http_status":None,"status":"unknown","failure_reason":None}
        try:
            url=ep["url"]
            if ep["method"]=="GET":
                params={"stock":code,"pageNum":1,"pageSize":5}
                url+="?"+"&".join(k+"="+str(v) for k,v in params.items())
                req=urllib.request.Request(url,headers=HEADERS)
            else:
                data=("stock="+code+"&pageNum=1&pageSize=5").encode()
                req=urllib.request.Request(ep["url"],data=data,headers={**HEADERS,"Content-Type":"application/x-www-form-urlencoded"})
            with urllib.request.urlopen(req,timeout=15) as resp:
                trial["http_status"]=resp.status
                body=resp.read()
                if resp.status==200 and len(body)>100:
                    trial["status"]="ok"
                    e["working_endpoints"].append(trial)
                else:
                    trial["status"]="low_content"
                    e["failed_endpoints"].append(trial)
        except urllib.error.HTTPError as ex:
            trial["http_status"]=ex.code;trial["status"]="failed";trial["failure_reason"]="http_"+str(ex.code)
            e["failed_endpoints"].append(trial)
        except Exception as ex:
            trial["status"]="failed";trial["failure_reason"]=str(ex)[:100]
            e["failed_endpoints"].append(trial)
    if e["working_endpoints"]: e["best_endpoint"]=e["working_endpoints"][0]["endpoint"]
    else: e["status"]="no_working_endpoint";e["failure_reason"]="all_endpoints_failed_or_http_500"
    return r
