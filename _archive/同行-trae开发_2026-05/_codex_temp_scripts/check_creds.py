#!/usr/bin/env python3
import sys
sys.path.insert(0, "/Users/apple/Documents/同行资本内容部门/内容生产系统/09_runbooks/scripts")

from market_wechat_publish_submit import load_credentials

creds = load_credentials("", "")
if creds:
    print(f"Credentials found: appid={creds[0][:4]}***")
else:
    print("No credentials found on this Mac")
    print("Checked paths:")
    from market_wechat_publish_submit import MAC_CREDENTIAL_PATHS
    for p in MAC_CREDENTIAL_PATHS:
        print(f"  {p}: exists={p.exists()}")
