import argparse,json,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","lib"))
def main():
    from smr_phase99_primary_source_retry import run_primary_retry
    from smr_phase99_fallback_execution import run_fallback_execution
    from smr_phase99_degraded_parser import run_degraded_parser
    from smr_phase99_alternative_field_mapping import run_alternative_field_mapping
    from smr_phase99_stale_source_refresh import run_stale_refresh
    from smr_phase99_blocked_source_replacement import run_blocked_replacement
    from smr_phase99_recovery_result_classifier import classify_recovery_results
    from smr_phase99_recovery_cannot_conclude_guard import run_recovery_guard
    retry=run_primary_retry("execute")
    fallback=run_fallback_execution(retry,"execute")
    degraded=run_degraded_parser("execute")
    fmap=run_alternative_field_mapping("execute")
    stale=run_stale_refresh("execute")
    repl=run_blocked_replacement("execute")
    cl=classify_recovery_results(retry,fallback,degraded,fmap,stale,repl)
    r=run_recovery_guard(cl)
    if "--json" in sys.argv:print(json.dumps(r,ensure_ascii=False,indent=2))
    else:print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
