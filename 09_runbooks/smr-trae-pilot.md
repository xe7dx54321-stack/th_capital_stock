# TRAE 试点验证流程

> 本文档记录 TRAE 与 SMR 系统集成的试点验证流程。
> **建议从日报任务开始试点，验证 3-5 天后再扩展到其他任务。**

---

## 试点计划

### 第一阶段：日报试点（Day 1-5）

**目标**：验证 TRAE 能正确读取数据、生成日报、写回系统

**验证清单**：

#### Day 1：首次执行
- [ ] TRAE Schedule 正确触发
- [ ] pnl.py 成功执行
- [ ] monitor.py 成功执行
- [ ] SQLite 查询返回正确数据
- [ ] 日报文件正确写入 `06_reports/daily/`
- [ ] register_snapshot 成功注册

#### Day 2-5：连续验证
- [ ] 每日日报格式一致
- [ ] 数据准确性（抽查）
- [ ] 快照正确注册到 registry
- [ ] 下游能读取日报内容

**验收标准**：
- 连续 5 天日报成功生成
- 数据准确率 ≥ 95%
- 无流程中断

---

### 第二阶段：扩展试点（Day 6-10）

**目标**：验证持仓复盘和风控检查任务

**验证清单**：

#### 持仓复盘任务
- [ ] 每笔持仓都有复盘记录
- [ ] thesis 状态判断合理
- [ ] 调仓建议有具体价格
- [ ] 复盘报告写入正确目录

#### 风控检查任务
- [ ] 风控参数检查完整
- [ ] 预警级别判断正确
- [ ] 风险说明写入正确目录
- [ ] 无预警时确认各指标正常

---

### 第三阶段：全量上线（Day 11+）

**目标**：稳定运行所有定时任务

**验证清单**：
- [ ] 所有 4 个任务稳定运行
- [ ] 周报生成正确
- [ ] 流程衔接无误
- [ ] 错误处理正常

---

## 验证方法

### 1. 检查文件生成

```bash
# 检查日报
ls -la th_capital_stock/06_reports/daily/

# 检查风控说明
ls -la th_capital_stock/05_risk/alerts/

# 检查复盘报告
ls -la th_capital_stock/04_portfolio/performance/
```

### 2. 检查快照注册

```bash
python -c "
import sqlite3, json
conn = sqlite3.connect('th_capital_stock/01_data/db/smr.db')
conn.row_factory = sqlite3.Row
entries = conn.execute('''
    SELECT * FROM task_registry_entry
    WHERE entity_type IN ('daily_report_candidate', 'risk_update_candidate', 'portfolio_review_snapshot')
    ORDER BY created_at DESC
    LIMIT 10
''').fetchall()
print(json.dumps([dict(r) for r in entries], ensure_ascii=False))
"
```

### 3. 检查数据准确性

抽查日报中的数据：
- 持仓盈亏是否与数据库一致
- 涨跌数据是否正确
- 风控参数计算是否正确

---

## 常见问题

### Q1：Schedule 没有触发
**检查项**：
- TRAE 是否正在运行
- Schedule 配置是否正确
- 网络连接是否正常

### Q2：脚本执行失败
**检查项**：
- Python 环境是否正确
- 依赖是否安装
- 路径是否正确

### Q3：日报数据不准确
**检查项**：
- 数据库数据是否最新
- 查询逻辑是否正确
- 时区是否正确

### Q4：快照注册失败
**检查项**：
- register_snapshot.py 是否存在
- 参数是否正确
- 数据库是否可写

---

## 试点结果记录

| 日期 | 任务 | 执行结果 | 问题 | 解决方案 |
|------|------|----------|------|----------|
| | | | | |

---

*最后更新：2026-06-18*
