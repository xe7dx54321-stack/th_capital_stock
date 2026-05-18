# SMR 东方财富公开研报结构化快照 Runbook

**更新日期**：2026-04-14  
**适用范围**：A 股公开研报的结构化字段抽取与统一 JSON 快照

---

## 1. 这条链做什么

这条链负责把已经落下来的：

- `research_article`（研报正文详情页）
- `research_pdf_text`（PDF 文本抽取）

进一步加工成：

- `research_structured`（研报结构化快照）

当前会统一抽出：

- 研报基础元数据
  - `info_code`
  - `title`
  - `published_at`
  - `org_name`
  - `researchers`
  - `rating_name`
  - `industry_name`
- 章节内容
  - `event`
  - `investment_points`
  - `forecast`
  - `risks`
- 关键预测字段
  - `revenue_billion`
  - `net_profit_billion`
  - `eps_yuan`
  - `pe_multiple`
  - `yoy_percent`
  - `target_price_yuan`
- 风险条目
- 关键词标签
- 上游来源引用

它的定位是把“可读文本”推进到“可直接消费的结构化输入”。

---

## 2. 前置依赖

必须先有：

```bash
python3 08_scripts/wiki/fetch_eastmoney_report_articles.py
python3 08_scripts/wiki/extract_eastmoney_report_pdf_text.py
```

---

## 3. 命令

默认跑法：

```bash
python3 08_scripts/wiki/extract_eastmoney_report_structured.py
python3 08_scripts/wiki/build_source_manifest.py
```

按指定标的构建：

```bash
python3 08_scripts/wiki/extract_eastmoney_report_structured.py \
  --ts-code 300308.SZ \
  --ts-code 300394.SZ \
  --report-limit 2
```

强制重建：

```bash
python3 08_scripts/wiki/extract_eastmoney_report_structured.py --force
```

---

## 4. 当前实现口径

- 以 `research_article` 为主来源切 section（章节）
- 以 `research_pdf_text` 为补充来源增强关键词与引用链
- 以东方财富原始 `search_item` 元数据补评级、目标价、EPS / PE 等字段
- 重点抽取 narrative forecast（叙述型盈利预测），不是逐格复原 PDF 表格
- 输出统一 JSON 原件和可读 Markdown 快照

---

## 5. 结果如何进入系统

构建完成后运行：

```bash
python3 08_scripts/wiki/build_source_manifest.py
```

这些结构化结果会进入 `source_manifest`，类型仍然是：

- `external_source_snapshot`

但 `source_kind` 会新增：

- `research_structured`

---

## 6. 当前真实状态

截至 `2026-04-14` 当前机器 4 只活跃 A 股都已经具备：

- `research_search = 1`
- `research_article = 2`
- `research_pdf = 2`
- `research_pdf_text = 2`
- `research_structured = 2`

当前重复跑验证结果：

- `persisted = 0`
- `skipped = 8`

说明这条链已经具备稳定的“已存在即跳过”能力。

---

## 7. 当前已知限制

- 当前已经有基础结构化，但还不是逐表格单元格复原
- PDF 里的复杂表格、图表、脚注还没有完全细粒度结构化；首版表格结构化已经拆到独立 runbook：
  - `09_runbooks/smr-eastmoney-report-table-structured-pipeline.md`
- 事实校验、跨来源去噪、评级冲突处理还没接上

所以它现在的定位是：

- **先给研究链提供稳定可消费的结构化输入**
- **先把评级、预测、风险、关键词这些高价值字段抽出来**
- **后续继续扩表格结构化覆盖率，再补事实校验**
