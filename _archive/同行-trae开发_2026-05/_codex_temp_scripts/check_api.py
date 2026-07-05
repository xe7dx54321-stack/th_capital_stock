#!/usr/bin/env python3
import sys
sys.path.insert(0, "/Users/apple/Documents/同行资本内容部门/内容生产系统/09_runbooks/scripts")

from market_wechat_publish_submit import load_credentials, WeChatOfficialClient

creds = load_credentials("", "")
if not creds:
    print("No credentials")
    sys.exit(1)

client = WeChatOfficialClient(*creds)
try:
    token = client.ensure_access_token()
    print(f"access_token obtained: {token[:10]}***")
    print("Mac can reach WeChat API - IP whitelist OK")
except RuntimeError as e:
    print(f"Failed to get access_token: {e}")
    if "40164" in str(e) or "ip" in str(e).lower():
        print("IP whitelist issue detected!")
