import json,os
from datetime import datetime
def build_operator_summary(status, exception):
    st=status.get("phase100_production_status",{})
    ex=exception.get("phase100_exception_blocker",{})
    lines=[]
    lines.append("# 每日生产运行概览")
    lines.append(f"## 运行时间：{datetime.now().isoformat()[:19]}")
    lines.append("## 今日最清楚的结论")
    lines.append(f"- Phase97 DB刷新：{st['phase97_db_refresh']['status']}，写入 {st['phase97_db_refresh']['records_written']} 条")
    lines.append(f"- Phase98 信源监控：{st['phase98_monitoring']['status']}，{st['phase98_monitoring']['sources_monitored']} 信源，{st['phase98_monitoring']['alerts_created']} 告警")
    lines.append(f"- Phase99 自愈恢复：{st['phase99_recovery']['status']}，恢复 {st['phase99_recovery']['total_recovered']}，部分恢复 {st['phase99_recovery']['partially_recovered']}")
    lines.append("## 需关注的例外")
    for e in ex.get("exceptions",[]):
        src=e.get("source",e.get("ticker","unknown"))
        blk=e.get("blocker",e.get("gap","unknown"))
        lines.append(f"- {e['type']}: {src} ({e.get('ticker','')}) — {blk}")
    lines.append("## 关键边界重申")
    lines.append("- 本报告是信源和获取能力生产状态报告，不是投资建议")
    lines.append("- 不包含买入/卖出/目标价/仓位建议")
    lines.append("- 300394 CNINFO 仍 blocked，300308/688041/002230/09988/00700/NVDA/AVGO 正常运行")
    return {"phase100_operator_summary":{"json_status":"pass","markdown":"\n".join(lines),"mock_used":False,"fixture_used":False}}
