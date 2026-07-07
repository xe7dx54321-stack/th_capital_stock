# TRAE Mac任务草案：投资报告撰写链

## 1. 任务基本信息

- **schedule_id**: `report_writing`
- **job_id**: `report_writing`
- **执行时间**: 14:00 每周一/三/五
- **牵头岗位**: `hermes_investment_report_writer`
- **参与岗位**: `hermes_investment_report_writer, openclaw_report_exec, hermes_reporting_editor`
- **超时时间**: 1800 秒
- **出错继续**: True
- **Prompt状态**: ✅ **完整**（使用模板 weekly_brief_task.md）
- **Registry状态**: ❌ **无Mac registry条目**（TRAE导出包额外记录）

---

## 2. Mac执行路径

### 2.1 手动触发（⚠️ **暂缓执行**）

```bash
cd /Users/apple/Documents/同行资本二级市场
python 08_scripts/scheduler/run_smr_schedule_job.py --job report_writing --dry-run
```

⚠️ **警告**: 此任务为defer_until_d7，暂不建议shadow-run。

---

## 3. 任务目标

生成周度总结报告，包含本周组合表现、最佳/最差持仓、Thesis 回顾、行业板块轮动、美股联动回顾、研究管线、下周展望七大章节。

---

## 4. 命令链（来源未确认）

⚠️ **注意**: run_smr_schedule_job.py中可能未定义此JobSpec。

**预期命令链**: Prompt模板中未提供具体命令链，需手动补充。

---

## 5. 输出产物

- 周报文件: `06_reports/weekly/weekly_{YYYY-MM-DD}.md`

---

## 6. 任务分类

- **分类**: ⚠️ **Defer_until_D7**
- **风险等级**: 高
- **判定依据**: 周报包含组合表现分析 + thesis回顾 + 下周展望

---

## 7. 暂缓原因

1. **包含组合表现分析**: 需确认Mac数据库与Windows数据一致性
2. **包含thesis回顾**: 需确认thesis回顾是否符合Foundation边界
3. **包含下周展望**: 需确认展望内容是否包含投资建议
4. **无Mac registry条目**: 需手动添加registry定义
5. **需等待D7**: Foundation输入流集成后才能保证数据一致性

---

## 8. Prompt路径映射

### 原始Prompt（Windows路径）

```bash
ls th_capital_stock/06_reports/daily/*.md
```

### Mac映射Prompt

```bash
ls 06_reports/daily/*.md  # 实际路径在Mac侧
```

---

## 9. Foundation边界检查

**检查项**:
- ❌ 周报是否包含目标价？
- ❌ 周报是否包含买入/卖出建议？
- ❌ 周报是否包含仓位建议？
- ❌ 下周展望是否包含投资建议？

**如发现边界违规**:
- 标记为永久defer
- 等待D7阶段foundation输入流集成
- 确保输出符合Foundation边界

---

## 10. 注意事项

- ✅ Prompt完整，有详细执行模板
- ❌ **Mac registry无此条目**，需手动添加
- ❌ **run_smr_schedule_job.py可能无此JobSpec**，需检查
- ⚠️ Prompt文件中bash示例有Windows硬编码路径，需手动替换为Mac路径
- ⚠️ **高风险**: 包含组合表现分析和thesis回顾，需严格审核
- ⚠️ **暂缓**: 等待D7阶段启用

---

## 11. 启用建议

**暂不建议Shadow-run**: 此任务包含组合表现分析和thesis回顾，风险高，需等待D7阶段。

**D7阶段启用步骤**:
1. 检查run_smr_schedule_job.py是否有report_writing JobSpec
2. 如无，手动添加JobSpec定义
3. 手动添加registry条目
4. 确认Mac数据库数据一致性
5. 确认Foundation输入流集成状态
6. 手动审核周报内容是否符合边界
7. 用户明确是否允许Mac侧运行报告撰写任务
8. 确认边界后正式启用

---

**Draft Generated**: 2026-07-07 21:50:00
**Draft Author**: TRAE Agent (GLM-5)