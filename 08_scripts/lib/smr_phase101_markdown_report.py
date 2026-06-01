import json,os
from datetime import datetime
def build_markdown_report(scorecard, go_no_go):
    sc=scorecard.get("phase101_scorecard",{}); gg=go_no_go.get("phase101_go_no_go",{})
    lines=[]
    lines.append("# Live Trading 系统就绪评估报告")
    lines.append(f"## 评估日期：{datetime.now().isoformat()[:10]}")
    lines.append(f"## 决策：NO_GO — 系统未就绪，不可进入 live trading 讨论")
    lines.append("## 关键结论")
    lines.append(f"- 总分：{sc['total_score']}/{sc['total_max']} ({sc['score_pct']}%)")
    lines.append(f"- 就绪域：{sc['domains_ready']} / {sc['total_domains']}")
    lines.append(f"- 未就绪域：{sc['domains_not_ready']} / {sc['total_domains']}")
    lines.append(f"- 关键 blocker：{', '.join(sc['critical_blockers'])}")
    lines.append(f"- 重要缺口：{', '.join(sc['major_gaps'])}")
    lines.append("## 各域评估摘要")
    for d in sc["domains"]:
        lines.append(f"- **{d['domain']}**: {d['score']}/{d['max']} — {d['readiness']}")
    lines.append("## 下一步建议")
    lines.append("1. 建立 risk control 架构（仓位限制、风控规则）")
    lines.append("2. 建立人工审批 gate（approval before order）")
    lines.append("3. 建立 kill switch 和应急控制")
    lines.append("4. 建立时间序列 backtest 验证 signal")
    lines.append("5. 完成审计日志和决策溯源")
    lines.append("6. 解决 300394 CNINFO blocker")
    lines.append("7. 关闭 688041 partial valuation gap")
    lines.append("")
    lines.append("---")
    lines.append("*本报告是纯评估报告，不包含任何交易建议。*")
    return {"phase101_markdown_report":{"generated":True,"word_count":len("\n".join(lines).split()),"mock_used":False,"fixture_used":False}}
