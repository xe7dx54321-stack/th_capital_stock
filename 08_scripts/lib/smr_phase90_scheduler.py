from smr_phase90_config import get_schedule,get_pipeline
def build_scheduler_commands():
    s=get_schedule();p=get_pipeline()
    home=str(__import__("pathlib").Path(__file__).resolve().parents[2])
    cmd=f"python {p['entry_point']} --execute --json"
    cmd_dry=f"python {p['entry_point']} --dry-run --json"
    cmd_skip=f"python {p['entry_point']} --skip-network --json"
    windows_task=f'schtasks /create /tn "Phase90_DailyIntelligence" /tr "cmd /c cd /d {home} && {cmd}" /sc DAILY /st {s["recommended_windows_time"]}'
    cron_line=f'{s["recommended_windows_time"][:2]} {s["recommended_windows_time"][3:]} * * {",".join(s["recommended_weekdays"])} cd {home} && {cmd} >> phase90_cron.log 2>&1'
    return {"phase90_scheduler_commands":{"schedule_enabled":s["enabled"],"mode":s["mode"],"commands":{"manual_execute":cmd,"manual_dry_run":cmd_dry,"skip_network":cmd_skip,"windows_task_scheduler":windows_task,"cron":cron_line},"note":"Windows Task Scheduler and cron commands require manual registration by user","mock_used":False,"fixture_used":False}}
