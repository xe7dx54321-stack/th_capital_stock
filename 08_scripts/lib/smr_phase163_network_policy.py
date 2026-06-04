def build_network_mode_policy(mode="skip-network"):
    return {"phase163_network_policy":{"mode":mode,"execute_network_allowed":mode=="execute","skip_network_supported":True,"lightweight_only":True,"max_concurrent":3,"rate_limit":"respectful","free_sources_only":True,"no_login_required":True,"no_automated_scraping":True,"raw_save_allowed":False,"mock_used":False,"fixture_used":False}}
