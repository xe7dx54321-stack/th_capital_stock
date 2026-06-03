def build_recovery_recommendation():
 recs={"if_console_fails":{"action":"run build_phase134_dashboard.py directly","severity":"critical"},"if_thesis_fails":{"action":"run build_phase138_thesis_library_board_report.py directly","severity":"critical"},"if_daily_brief_fails":{"action":"skip_and_continue_degraded","severity":"degradable"},"common_fixes":["check_python_path","verify_config_exists","recompile_lib_files","run_tests_before_delivery"]}
 return {"phase140_recovery_recommendation_builder":{"recommendations":recs,"ready":True,"mock_used":False,"fixture_used":False}}
