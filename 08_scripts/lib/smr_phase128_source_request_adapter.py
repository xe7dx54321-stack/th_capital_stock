import urllib.request,urllib.error,socket,json,ssl

def probe_url(url,method="HEAD",timeout=15):
    result={"url":url,"method":method,"status":"unknown","http_code":None,"error":None,"reachable":False}
    ctx=ssl.create_default_context()
    ctx.check_hostname=False
    ctx.verify_mode=ssl.CERT_NONE
    try:
        req=urllib.request.Request(url,method=method,headers={"User-Agent":"th_capital_research/1.0"})
        resp=urllib.request.urlopen(req,timeout=timeout,context=ctx)
        result["http_code"]=resp.getcode()
        result["reachable"]=resp.getcode()<400
        result["status"]="available" if result["reachable"] else "blocked"
        result["content_type"]=resp.headers.get("Content-Type","")
    except urllib.error.HTTPError as e:
        result["http_code"]=e.code
        result["error"]=f"HTTP {e.code}: {e.reason}"
        result["status"]="blocked"
        result["reachable"]=False
    except urllib.error.URLError as e:
        result["error"]=f"URL Error: {e.reason}"
        result["status"]="blocked"
        result["reachable"]=False
    except socket.timeout:
        result["error"]="Timeout"
        result["status"]="blocked"
        result["reachable"]=False
    except Exception as e:
        result["error"]=str(e)[:200]
        result["status"]="blocked"
        result["reachable"]=False
    return result

def build_request_adapter():
    return {"phase128_source_request_adapter":{"capabilities":["HEAD","GET"],"max_timeout":15,"user_agent":"th_capital_research/1.0","save_raw":False,"mock_used":False,"fixture_used":False}}
